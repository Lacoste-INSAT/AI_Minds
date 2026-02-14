"""
Synapsis Backend — Graph Service
NetworkX-based in-memory graph + SQLite persistence.
"""

from __future__ import annotations

import json
from typing import Any

import networkx as nx
import structlog

from backend.database import get_db
from backend.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

# In-memory graph
_graph: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    """Get or build the in-memory graph from SQLite."""
    global _graph
    if _graph is None:
        _graph = _load_graph_from_db()
    return _graph


def _load_graph_from_db() -> nx.DiGraph:
    """Load nodes and edges from SQLite into NetworkX."""
    G = nx.DiGraph()

    with get_db() as conn:
        # Load nodes
        rows = conn.execute("SELECT id, type, name, properties, mention_count FROM nodes").fetchall()
        for row in rows:
            props = json.loads(row["properties"]) if row["properties"] else {}
            G.add_node(
                row["id"],
                type=row["type"],
                name=row["name"],
                mention_count=row["mention_count"],
                **props,
            )

        # Load edges
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

    logger.info("graph.loaded", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    return G


def reload_graph():
    """Force-reload the graph from DB."""
    global _graph
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
    """Add or update a node. Returns node ID."""
    G = get_graph()
    name_lower = name.lower().strip()

    # Check if node already exists by name
    existing_id = find_node_by_name(name_lower)

    with get_db() as conn:
        if existing_id:
            # Update existing node
            conn.execute(
                """UPDATE nodes SET last_seen = ?, mention_count = mention_count + 1,
                   source_chunks = CASE
                       WHEN source_chunks IS NULL THEN ?
                       ELSE source_chunks || ',' || ?
                   END
                   WHERE id = ?""",
                (utc_now(), source_chunk_id or "", source_chunk_id or "", existing_id),
            )
            # Update in-memory
            if existing_id in G.nodes:
                G.nodes[existing_id]["mention_count"] = G.nodes[existing_id].get("mention_count", 1) + 1
            return existing_id
        else:
            # Create new node
            node_id = generate_id()
            now = utc_now()
            conn.execute(
                """INSERT INTO nodes (id, type, name, properties, first_seen, last_seen, mention_count, source_chunks)
                   VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
                (
                    node_id,
                    node_type,
                    name_lower,
                    json.dumps(properties) if properties else None,
                    now,
                    now,
                    source_chunk_id or "",
                ),
            )
            # Add to in-memory graph
            G.add_node(
                node_id,
                type=node_type,
                name=name_lower,
                mention_count=1,
                **(properties or {}),
            )
            return node_id


def find_node_by_name(name: str) -> str | None:
    """Find a node ID by name (case-insensitive)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT id FROM nodes WHERE LOWER(name) = LOWER(?)", (name.strip(),)
        ).fetchone()
        return row["id"] if row else None


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
    """Add an edge between two nodes. Returns edge ID."""
    G = get_graph()
    edge_id = generate_id()

    with get_db() as conn:
        # Check if edge already exists
        existing = conn.execute(
            """SELECT id FROM edges WHERE source_id = ? AND target_id = ? AND relationship = ?""",
            (source_id, target_id, relationship),
        ).fetchone()

        if existing:
            return existing["id"]

        conn.execute(
            """INSERT INTO edges (id, source_id, target_id, relationship, properties, created_at, source_chunk)
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

    # Add to in-memory graph
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
    """Get chunk IDs associated with an entity."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT source_chunks FROM nodes WHERE LOWER(name) = LOWER(?)",
            (node_name.strip(),),
        ).fetchone()
        if row and row["source_chunks"]:
            return [c for c in row["source_chunks"].split(",") if c]
    return []
