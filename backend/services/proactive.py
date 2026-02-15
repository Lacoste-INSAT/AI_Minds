"""
Synapsis Backend — Proactive Insights Engine
Connection discovery, contradiction detection, digest generation, pattern alerts.
"""

from __future__ import annotations

import json

import structlog

from backend.database import get_db, log_audit
from backend.utils.helpers import generate_id, utc_now
from backend.services.model_router import ModelTask, generate_for_task, ensure_lane

logger = structlog.get_logger(__name__)

# In-memory store for recent insights
_insights: list[dict] = []
_loaded = False


def get_recent_insights(limit: int = 20) -> list[dict]:
    """Get the most recent insights."""
    _load_insights_once()
    return _insights[-limit:] if _insights else []


def _add_insight(insight_type: str, title: str, description: str, entities: list[str] | None = None):
    """Add an insight to the store."""
    _load_insights_once()
    insight = {
        "id": generate_id(),
        "type": insight_type,
        "title": title,
        "description": description,
        "related_entities": entities or [],
        "created_at": utc_now(),
    }
    _insights.append(insight)

    # Cap list size to prevent unbounded memory growth
    _MAX_INSIGHTS = 500
    if len(_insights) > _MAX_INSIGHTS:
        del _insights[:-_MAX_INSIGHTS]

    with get_db() as conn:
        conn.execute(
            """INSERT INTO proactive_insights (id, type, title, description, related_entities, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                insight["id"],
                insight["type"],
                insight["title"],
                insight["description"],
                json.dumps(insight["related_entities"]),
                insight["created_at"],
            ),
        )

    log_audit("insight_generated", insight)
    logger.info("proactive.insight", type=insight_type, title=title)


def _load_insights_once() -> None:
    global _loaded
    if _loaded:
        return
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, type, title, description, related_entities, created_at
               FROM proactive_insights
               ORDER BY created_at ASC
               LIMIT 500"""
        ).fetchall()
    for row in rows:
        _insights.append(
            {
                "id": row["id"],
                "type": row["type"],
                "title": row["title"],
                "description": row["description"],
                "related_entities": json.loads(row["related_entities"]) if row["related_entities"] else [],
                "created_at": row["created_at"],
            }
        )
    _loaded = True


# ---------------------------------------------------------------------------
# Connection Discovery (post-ingestion hook)
# ---------------------------------------------------------------------------


async def discover_connections(new_entities: list[str]) -> list[dict]:
    """
    Check if newly ingested entities connect to existing graph clusters.
    Called after each file ingestion.
    """
    if not new_entities:
        return []

    from backend.services.graph_service import get_graph

    G = get_graph()
    connections = []

    for entity_name in new_entities:
        entity_lower = entity_name.lower().strip()

        # Find existing node
        node_id = None
        for nid, data in G.nodes(data=True):
            if data.get("name", "").lower() == entity_lower:
                node_id = nid
                break

        if node_id and G.degree(node_id) > 1:
            neighbors = list(G.neighbors(node_id)) + list(G.predecessors(node_id))
            unique_neighbors = set(neighbors)

            if len(unique_neighbors) >= 2:
                neighbor_names = [
                    G.nodes[n].get("name", "unknown")
                    for n in list(unique_neighbors)[:5]
                ]
                conn = {
                    "entity": entity_name,
                    "connections": neighbor_names,
                    "count": len(unique_neighbors),
                }
                connections.append(conn)

                _add_insight(
                    "connection",
                    f"'{entity_name}' connects to {len(unique_neighbors)} other concepts",
                    f"Your new content about '{entity_name}' connects to: {', '.join(neighbor_names)}",
                    [entity_name] + neighbor_names,
                )

    return connections


# ---------------------------------------------------------------------------
# Contradiction Detection (post-ingestion hook)
# ---------------------------------------------------------------------------


async def detect_contradictions(document_id: str) -> list[dict]:
    """
    Compare new beliefs against existing beliefs for the same entity.
    """
    contradictions = []

    with get_db() as conn:
        # Get entities from the new document's chunks
        chunk_rows = conn.execute(
            "SELECT id, content FROM chunks WHERE document_id = ?", (document_id,)
        ).fetchall()

    if not chunk_rows:
        return contradictions

    # Get existing beliefs
    with get_db() as conn:
        beliefs = conn.execute(
            "SELECT b.id, b.belief, b.node_id, n.name, b.timestamp "
            "FROM beliefs b JOIN nodes n ON b.node_id = n.id "
            "ORDER BY b.timestamp DESC"
        ).fetchall()

    if not beliefs:
        return contradictions

    # Use LLM to detect contradictions between new content and existing beliefs
    lane_ok, _ = await ensure_lane(ModelTask.background_proactive, operation="proactive_contradictions")
    if not lane_ok:
        return contradictions

    try:
        new_content = " ".join(r["content"] for r in chunk_rows)[:2000]
        existing_beliefs_text = "\n".join(
            f"- [{b['name']}]: {b['belief']} (from {b['timestamp']})"
            for b in beliefs[:10]
        )

        if not existing_beliefs_text.strip():
            return contradictions

        prompt = f"""Compare these new statements with existing beliefs and identify contradictions.

New content:
{new_content}

Existing beliefs:
{existing_beliefs_text}

If there are contradictions, respond with JSON:
{{"contradictions": [{{"entity": "name", "old_belief": "...", "new_belief": "...", "explanation": "..."}}]}}

If no contradictions, respond: {{"contradictions": []}}
"""

        response = await generate_for_task(
            task=ModelTask.background_proactive,
            prompt=prompt,
            system="You are a contradiction detection agent. Return ONLY valid JSON.",
            temperature=0.1,
            max_tokens=512,
            operation="proactive_contradictions",
        )

        import re
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            data = json.loads(json_match.group())
            for c in data.get("contradictions", []):
                contradictions.append(c)
                _add_insight(
                    "contradiction",
                    f"Contradiction found for '{c.get('entity', 'unknown')}'",
                    f"Old: {c.get('old_belief', '')} → New: {c.get('new_belief', '')}. {c.get('explanation', '')}",
                    [c.get("entity", "")],
                )

    except Exception as e:
        logger.warning("proactive.contradiction_detection_failed", error=str(e))

    return contradictions


# ---------------------------------------------------------------------------
# Digest Generation (scheduled)
# ---------------------------------------------------------------------------


async def generate_digest() -> dict:
    """
    Generate a digest of recent activity — topic frequencies, patterns.
    """
    digest = {
        "generated_at": utc_now(),
        "summary": "",
        "topic_mentions": {},
        "recent_entities": [],
        "total_documents": 0,
    }

    with get_db() as conn:
        # Count documents
        count = conn.execute("SELECT COUNT(*) as c FROM documents WHERE status = 'processed'").fetchone()
        digest["total_documents"] = count["c"] if count else 0

        # Get recent categories
        categories = conn.execute(
            "SELECT category, COUNT(*) as c FROM chunks WHERE category IS NOT NULL GROUP BY category ORDER BY c DESC"
        ).fetchall()
        digest["topic_mentions"] = {r["category"]: r["c"] for r in categories}

        # Get top entities by mention count
        entities = conn.execute(
            "SELECT name, type, mention_count FROM nodes ORDER BY mention_count DESC LIMIT 10"
        ).fetchall()
        digest["recent_entities"] = [
            {"name": e["name"], "type": e["type"], "mentions": e["mention_count"]}
            for e in entities
        ]

    # Generate narrative summary via LLM
    lane_ok, _ = await ensure_lane(ModelTask.background_proactive, operation="proactive_digest")
    if not lane_ok:
        digest["summary"] = f"You have {digest['total_documents']} documents ingested."
        return digest

    try:
        topics = ", ".join(f"{k} ({v} mentions)" for k, v in digest["topic_mentions"].items())
        entities_str = ", ".join(f"{e['name']} ({e['mentions']}x)" for e in digest["recent_entities"])

        prompt = f"""Generate a brief digest summary (2-3 sentences) of this user's recent knowledge activity.

Topics: {topics if topics else 'None yet'}
Top entities: {entities_str if entities_str else 'None yet'}
Total documents: {digest['total_documents']}

Be conversational and insightful. Highlight notable patterns."""

        summary = await generate_for_task(
            task=ModelTask.background_proactive,
            prompt=prompt,
            system="You are a helpful knowledge digest assistant. Be concise and insightful.",
            temperature=0.4,
            max_tokens=256,
            operation="proactive_digest",
        )
        digest["summary"] = summary.strip()
    except Exception as e:
        logger.warning("proactive.digest_generation_failed", error=str(e))
        digest["summary"] = f"You have {digest['total_documents']} documents ingested."

    _add_insight(
        "digest",
        "Knowledge Digest",
        digest["summary"],
        [e["name"] for e in digest["recent_entities"]],
    )

    return digest


# ---------------------------------------------------------------------------
# Pattern Detection (scheduled)
# ---------------------------------------------------------------------------


async def detect_patterns() -> list[dict]:
    """Detect patterns using NetworkX centrality analysis."""
    patterns = []

    try:
        from backend.services.graph_service import get_graph
        import networkx as nx

        G = get_graph()
        if G.number_of_nodes() < 3:
            return patterns

        # Find central entities (most connected)
        try:
            centrality = nx.degree_centrality(G)
            top_central = sorted(centrality.items(), key=lambda x: x[1], reverse=True)[:5]

            for node_id, score in top_central:
                if score > 0.1:
                    name = G.nodes[node_id].get("name", "unknown")
                    patterns.append({
                        "type": "central_entity",
                        "entity": name,
                        "centrality_score": round(score, 3),
                    })
                    _add_insight(
                        "pattern",
                        f"'{name}' is a central concept",
                        f"'{name}' is highly connected in your knowledge graph (centrality: {round(score, 3)})",
                        [name],
                    )
        except Exception:
            pass

        # Find communities / clusters
        try:
            undirected = G.to_undirected()
            if undirected.number_of_edges() > 0:
                communities = list(nx.connected_components(undirected))
                for i, community in enumerate(communities[:5]):
                    if len(community) >= 3:
                        names = [G.nodes[n].get("name", "unknown") for n in list(community)[:5]]
                        patterns.append({
                            "type": "cluster",
                            "entities": names,
                            "size": len(community),
                        })
        except Exception:
            pass

    except Exception as e:
        logger.warning("proactive.pattern_detection_failed", error=str(e))

    return patterns
