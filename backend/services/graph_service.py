"""
Synapsis Backend — Graph Service
NetworkX-based in-memory graph + SQLite persistence.

Thread-safe via ``_graph_lock``.  Name→ID lookups are cached to avoid N+1
queries during ingestion.  Node↔chunk associations use the ``node_chunks``
junction table instead of the old comma-separated ``source_chunks`` column.
"""

from __future__ import annotations

import json
import threading
from typing import Any

import networkx as nx
import structlog

from backend.database import get_db
from backend.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Thread-safe graph singleton
# ---------------------------------------------------------------------------

_graph: nx.DiGraph | None = None
_graph_lock = threading.Lock()

# Name → node-id cache (lowercase name → id).  Populated on graph load and
# kept in sync by ``add_node``.  Protected by ``_graph_lock``.
_name_cache: dict[str, str] = {}


def get_graph() -> nx.DiGraph:
    """Get or build the in-memory graph from SQLite (thread-safe)."""
    global _graph
    if _graph is None:
        with _graph_lock:
            # Double-checked locking
            if _graph is None:
                _graph = _load_graph_from_db()
    return _graph


def _load_graph_from_db() -> nx.DiGraph:
    """Load nodes and edges from SQLite into NetworkX."""
    global _name_cache

    G = nx.DiGraph()
    cache: dict[str, str] = {}

    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, type, name, properties, mention_count FROM nodes"
        ).fetchall()
        for row in rows:
            props = json.loads(row["properties"]) if row["properties"] else {}
            G.add_node(
                row["id"],
                type=row["type"],
                name=row["name"],
                mention_count=row["mention_count"],
                **props,
            )
            cache[row["name"].lower().strip()] = row["id"]

        rows = conn.execute(
            "SELECT id, source_id, target_id, relationship, properties FROM edges"
        ).fetchall()
        for row in rows:
            props = json.loads(row["properties"]) if row["properties"] else {}
            G.add_edge(
                row["source_id"],
                row["target_id"],
                id=row["id"],
                relationship=row["relationship"],
                **props,
            )

    _name_cache = cache
    logger.info("graph.loaded", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def reload_graph():
    """Force-reload the graph from DB (thread-safe)."""
    global _graph
    with _graph_lock:
        _graph = _load_graph_from_db()


# ---------------------------------------------------------------------------
# Node operations
# ---------------------------------------------------------------------------


def add_node(
    name: str,
    node_type: str,
    properties: dict | None = None,
    source_chunk_id: str | None = None,
) -> str:
    """Add or update a node.  Returns node ID.

    Uses the ``node_chunks`` junction table for chunk associations.
    """
    name_lower = name.lower().strip()
    if not name_lower:
        raise ValueError("Entity name must not be empty")

    with _graph_lock:
        G = get_graph()
        existing_id = _name_cache.get(name_lower)

        with get_db() as conn:
            if existing_id:
                conn.execute(
                    "UPDATE nodes SET last_seen = ?, mention_count = mention_count + 1 WHERE id = ?",
                    (utc_now(), existing_id),
                )
                if source_chunk_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO node_chunks (node_id, chunk_id) VALUES (?, ?)",
                        (existing_id, source_chunk_id),
                    )
                # Update in-memory
                if existing_id in G.nodes:
                    G.nodes[existing_id]["mention_count"] = (
                        G.nodes[existing_id].get("mention_count", 1) + 1
                    )
                return existing_id
            else:
                node_id = generate_id()
                now = utc_now()
                conn.execute(
                    """INSERT INTO nodes
                       (id, type, name, properties, first_seen, last_seen, mention_count, source_chunks)
                       VALUES (?, ?, ?, ?, ?, ?, 1, '')""",
                    (
                        node_id,
                        node_type,
                        name_lower,
                        json.dumps(properties) if properties else None,
                        now,
                        now,
                    ),
                )
                if source_chunk_id:
                    conn.execute(
                        "INSERT OR IGNORE INTO node_chunks (node_id, chunk_id) VALUES (?, ?)",
                        (node_id, source_chunk_id),
                    )

                # In-memory updates (inside lock, after successful DB write)
                G.add_node(
                    node_id,
                    type=node_type,
                    name=name_lower,
                    mention_count=1,
                    **(properties or {}),
                )
                _name_cache[name_lower] = node_id
                return node_id


def find_node_by_name(name: str) -> str | None:
    """Find a node ID by name (case-insensitive).

    Uses the in-memory cache — O(1) instead of a DB round-trip.
    Falls back to DB if the cache misses.
    """
    key = name.lower().strip()

    # Fast path: cache hit
    cached = _name_cache.get(key)
    if cached is not None:
        return cached

    # Slow path: DB fallback (keeps cache warm)
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM nodes WHERE LOWER(name) = LOWER(?)", (key,)
        ).fetchone()
        if row:
            with _graph_lock:
                _name_cache[key] = row["id"]
            return row["id"]

    return None


# ---------------------------------------------------------------------------
# Edge operations
# ---------------------------------------------------------------------------


def add_edge(
    source_id: str,
    target_id: str,
    relationship: str,
    properties: dict | None = None,
    source_chunk_id: str | None = None,
) -> str:
    """Add an edge between two nodes.  Returns edge ID.

    Uses UNIQUE(source_id, target_id, relationship) constraint to
    avoid duplicates.  In-memory graph is only updated after the DB
    write succeeds, inside the same lock scope.
    """
    edge_id = generate_id()

    with _graph_lock:
        G = get_graph()

        with get_db() as conn:
            # Check if edge already exists
            existing = conn.execute(
                "SELECT id FROM edges WHERE source_id = ? AND target_id = ? AND relationship = ?",
                (source_id, target_id, relationship),
            ).fetchone()

            if existing:
                return existing["id"]

            conn.execute(
                """INSERT INTO edges
                   (id, source_id, target_id, relationship, properties, created_at, source_chunk)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    edge_id,
                    source_id,
                    target_id,
                    relationship,
                    json.dumps(properties) if properties else None,
                    utc_now(),
                    source_chunk_id,
                ),
            )

        # DB commit succeeded — now update in-memory graph (still under lock)
        G.add_edge(
            source_id,
            target_id,
            id=edge_id,
            relationship=relationship,
            **(properties or {}),
        )

    return edge_id


# ---------------------------------------------------------------------------
# Graph queries
# ---------------------------------------------------------------------------


def get_graph_data(limit: int = 200) -> dict:
    """Get graph data for frontend visualization."""
    with get_db() as conn:
        nodes = conn.execute(
            "SELECT id, type, name, properties, mention_count FROM nodes ORDER BY mention_count DESC LIMIT ?",
            (limit,),
        ).fetchall()

        node_ids = {n["id"] for n in nodes}

        edges = conn.execute(
            "SELECT id, source_id, target_id, relationship, properties FROM edges"
        ).fetchall()

    graph_nodes = []
    for n in nodes:
        graph_nodes.append({
            "id": n["id"],
            "type": n["type"],
            "name": n["name"],
            "properties": json.loads(n["properties"]) if n["properties"] else None,
            "mention_count": n["mention_count"],
        })

    graph_edges = []
    for e in edges:
        if e["source_id"] in node_ids and e["target_id"] in node_ids:
            graph_edges.append({
                "id": e["id"],
                "source": e["source_id"],
                "target": e["target_id"],
                "relationship": e["relationship"],
                "properties": json.loads(e["properties"]) if e["properties"] else None,
            })

    return {"nodes": graph_nodes, "edges": graph_edges}


def find_paths(
    source_name: str,
    target_name: str,
    max_depth: int = 3,
) -> list[list[str]]:
    """Find all simple paths between two named entities."""
    G = get_graph()

    source_id = find_node_by_name(source_name)
    target_id = find_node_by_name(target_name)

    if not source_id or not target_id:
        return []

    try:
        paths = list(nx.all_simple_paths(G, source_id, target_id, cutoff=max_depth))
        return paths
    except nx.NetworkXError:
        return []


def get_neighbors(node_name: str, depth: int = 1) -> dict:
    """Get the neighborhood of a named entity."""
    G = get_graph()
    node_id = find_node_by_name(node_name)

    if not node_id or node_id not in G:
        return {"nodes": [], "edges": []}

    # BFS to depth
    visited = {node_id}
    frontier = {node_id}

    for _ in range(depth):
        next_frontier = set()
        for n in frontier:
            next_frontier.update(G.successors(n))
            next_frontier.update(G.predecessors(n))
        frontier = next_frontier - visited
        visited.update(frontier)

    # Build subgraph
    subgraph = G.subgraph(visited)

    nodes = []
    for n in subgraph.nodes(data=True):
        nodes.append({
            "id": n[0],
            "type": n[1].get("type", "unknown"),
            "name": n[1].get("name", ""),
            "mention_count": n[1].get("mention_count", 1),
        })

    edges = []
    for u, v, data in subgraph.edges(data=True):
        edges.append({
            "id": data.get("id", ""),
            "source": u,
            "target": v,
            "relationship": data.get("relationship", ""),
        })

    return {"nodes": nodes, "edges": edges}


def get_entity_chunks(node_name: str) -> list[str]:
    """Get chunk IDs associated with an entity via the junction table."""
    node_id = find_node_by_name(node_name)
    if not node_id:
        return []

    with get_db() as conn:
        rows = conn.execute(
            "SELECT chunk_id FROM node_chunks WHERE node_id = ?",
            (node_id,),
        ).fetchall()
    return [r["chunk_id"] for r in rows]


# ---------------------------------------------------------------------------
# Graph analytics — centrality, communities, similarity
# ---------------------------------------------------------------------------


def get_centrality_metrics(top_k: int = 20) -> dict:
    """
    Compute graph centrality metrics for all nodes.

    Returns:
        dict with "degree", "betweenness", "pagerank" — each a list of
        ``{"id", "name", "type", "score"}`` sorted desc.
    """
    G = get_graph()
    if G.number_of_nodes() == 0:
        return {"degree": [], "betweenness": [], "pagerank": []}

    def _top(scores: dict[str, float]) -> list[dict]:
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        results = []
        for node_id, score in ranked:
            data = G.nodes.get(node_id, {})
            results.append({
                "id": node_id,
                "name": data.get("name", ""),
                "type": data.get("type", ""),
                "score": round(score, 6),
            })
        return results

    # Degree centrality (in + out)
    degree = nx.degree_centrality(G)

    # Betweenness centrality
    try:
        betweenness = nx.betweenness_centrality(G, k=min(100, G.number_of_nodes()))
    except Exception:
        betweenness = {n: 0.0 for n in G.nodes}

    # PageRank
    try:
        pagerank = nx.pagerank(G, max_iter=100)
    except Exception:
        pagerank = {n: 1.0 / max(G.number_of_nodes(), 1) for n in G.nodes}

    return {
        "degree": _top(degree),
        "betweenness": _top(betweenness),
        "pagerank": _top(pagerank),
    }


def detect_communities() -> list[list[dict]]:
    """
    Detect communities using label propagation on the undirected projection.

    Returns a list of communities, where each community is a list of
    ``{"id", "name", "type", "mention_count"}`` dicts, sorted largest first.
    """
    G = get_graph()
    if G.number_of_nodes() == 0:
        return []

    undirected = G.to_undirected()

    try:
        communities_gen = nx.community.label_propagation_communities(undirected)
    except Exception:
        # Fallback: connected components
        communities_gen = nx.connected_components(undirected)

    result = []
    for community_set in communities_gen:
        members = []
        for node_id in community_set:
            data = G.nodes.get(node_id, {})
            members.append({
                "id": node_id,
                "name": data.get("name", ""),
                "type": data.get("type", ""),
                "mention_count": data.get("mention_count", 1),
            })
        members.sort(key=lambda x: x["mention_count"], reverse=True)
        result.append(members)

    result.sort(key=len, reverse=True)
    return result


def get_entity_similarity(entity_name: str, top_k: int = 10) -> list[dict]:
    """
    Find most similar entities based on Jaccard similarity of neighborhoods.

    Two entities are similar if they share many neighbours in the graph.
    """
    G = get_graph()
    node_id = find_node_by_name(entity_name)

    if not node_id or node_id not in G:
        return []

    # Neighbours of target (union of successors / predecessors)
    target_neighbors = set(G.successors(node_id)) | set(G.predecessors(node_id))
    if not target_neighbors:
        return []

    scores: list[tuple[str, float]] = []
    for other_id in G.nodes:
        if other_id == node_id:
            continue
        other_neighbors = set(G.successors(other_id)) | set(G.predecessors(other_id))
        if not other_neighbors:
            continue

        intersection = target_neighbors & other_neighbors
        union = target_neighbors | other_neighbors
        jaccard = len(intersection) / len(union) if union else 0.0
        if jaccard > 0.0:
            scores.append((other_id, jaccard))

    scores.sort(key=lambda x: x[1], reverse=True)

    result = []
    for nid, score in scores[:top_k]:
        data = G.nodes.get(nid, {})
        result.append({
            "id": nid,
            "name": data.get("name", ""),
            "type": data.get("type", ""),
            "similarity": round(score, 4),
        })

    return result


def get_subgraph_for_entities(entity_names: list[str], max_depth: int = 1) -> dict:
    """
    Extract a subgraph containing the given entities and their neighborhoods.

    Useful for building contextual subgraphs for LLM prompts.
    """
    G = get_graph()
    seed_ids: set[str] = set()

    for name in entity_names:
        nid = find_node_by_name(name)
        if nid and nid in G:
            seed_ids.add(nid)

    if not seed_ids:
        return {"nodes": [], "edges": []}

    # BFS from all seeds
    visited = set(seed_ids)
    frontier = set(seed_ids)

    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for n in frontier:
            next_frontier.update(G.successors(n))
            next_frontier.update(G.predecessors(n))
        frontier = next_frontier - visited
        visited.update(frontier)

    subgraph = G.subgraph(visited)

    nodes = []
    for n, data in subgraph.nodes(data=True):
        nodes.append({
            "id": n,
            "type": data.get("type", "unknown"),
            "name": data.get("name", ""),
            "mention_count": data.get("mention_count", 1),
            "is_seed": n in seed_ids,
        })

    edges = []
    for u, v, data in subgraph.edges(data=True):
        edges.append({
            "id": data.get("id", ""),
            "source": u,
            "target": v,
            "relationship": data.get("relationship", ""),
        })

    return {"nodes": nodes, "edges": edges}


def get_graph_stats() -> dict:
    """Compute summary statistics about the knowledge graph."""
    G = get_graph()

    stats: dict[str, Any] = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "density": round(nx.density(G), 6) if G.number_of_nodes() > 1 else 0.0,
    }

    if G.number_of_nodes() > 0:
        undirected = G.to_undirected()
        components = list(nx.connected_components(undirected))
        stats["connected_components"] = len(components)
        stats["largest_component_size"] = max(len(c) for c in components)

        # Degree distribution
        degrees = [d for _, d in G.degree()]
        stats["avg_degree"] = round(sum(degrees) / len(degrees), 2) if degrees else 0.0
        stats["max_degree"] = max(degrees) if degrees else 0

        # Node type distribution
        type_counts: dict[str, int] = {}
        for _, data in G.nodes(data=True):
            t = data.get("type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1
        stats["node_types"] = type_counts

        # Relationship type distribution
        rel_counts: dict[str, int] = {}
        for _, _, data in G.edges(data=True):
            r = data.get("relationship", "unknown")
            rel_counts[r] = rel_counts.get(r, 0) + 1
        stats["relationship_types"] = rel_counts

    else:
        stats["connected_components"] = 0
        stats["largest_component_size"] = 0
        stats["avg_degree"] = 0.0
        stats["max_degree"] = 0
        stats["node_types"] = {}
        stats["relationship_types"] = {}

    return stats
