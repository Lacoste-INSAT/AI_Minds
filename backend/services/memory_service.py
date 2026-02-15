"""
Synapsis Backend — Structured Memory Service
High-level CRUD operations over the SQLite memory store.

Provides:
- Entity (node) management: search, get, merge, delete
- Relationship (edge) management: create, query, delete
- Belief tracking: add, supersede, query
- Document ↔ entity lookups
- Full-text memory search across chunks
- Statistics and analytics
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from backend.database import get_db, log_audit
from backend.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Entity (node) CRUD
# ---------------------------------------------------------------------------


def get_entity(entity_id: str) -> dict | None:
    """Get a single entity by ID with all its relationships."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM nodes WHERE id = ?", (entity_id,)
        ).fetchone()
        if not row:
            return None

        # Get outgoing edges
        outgoing = conn.execute(
            """SELECT e.id, e.target_id, n.name as target_name, n.type as target_type,
                      e.relationship, e.properties, e.created_at
               FROM edges e JOIN nodes n ON e.target_id = n.id
               WHERE e.source_id = ?""",
            (entity_id,),
        ).fetchall()

        # Get incoming edges
        incoming = conn.execute(
            """SELECT e.id, e.source_id, n.name as source_name, n.type as source_type,
                      e.relationship, e.properties, e.created_at
               FROM edges e JOIN nodes n ON e.source_id = n.id
               WHERE e.target_id = ?""",
            (entity_id,),
        ).fetchall()

        # Get beliefs
        beliefs = conn.execute(
            """SELECT id, belief, confidence, timestamp, superseded_by
               FROM beliefs WHERE node_id = ? AND superseded_by IS NULL
               ORDER BY timestamp DESC""",
            (entity_id,),
        ).fetchall()

    return {
        "id": row["id"],
        "type": row["type"],
        "name": row["name"],
        "properties": json.loads(row["properties"]) if row["properties"] else {},
        "first_seen": row["first_seen"],
        "last_seen": row["last_seen"],
        "mention_count": row["mention_count"],
        "outgoing_edges": [
            {
                "id": e["id"],
                "target_id": e["target_id"],
                "target_name": e["target_name"],
                "target_type": e["target_type"],
                "relationship": e["relationship"],
                "properties": json.loads(e["properties"]) if e["properties"] else {},
                "created_at": e["created_at"],
            }
            for e in outgoing
        ],
        "incoming_edges": [
            {
                "id": e["id"],
                "source_id": e["source_id"],
                "source_name": e["source_name"],
                "source_type": e["source_type"],
                "relationship": e["relationship"],
                "properties": json.loads(e["properties"]) if e["properties"] else {},
                "created_at": e["created_at"],
            }
            for e in incoming
        ],
        "beliefs": [
            {
                "id": b["id"],
                "belief": b["belief"],
                "confidence": b["confidence"],
                "timestamp": b["timestamp"],
            }
            for b in beliefs
        ],
    }


def search_entities(
    query: str | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: str = "mention_count",  # "mention_count" | "last_seen" | "name"
) -> dict:
    """Search entities with optional type filter and text search."""
    where = []
    params: list[Any] = []

    if query:
        where.append("LOWER(name) LIKE ?")
        params.append(f"%{query.lower()}%")

    if entity_type:
        where.append("type = ?")
        params.append(entity_type)

    where_sql = " AND ".join(where) if where else "1=1"

    valid_sorts = {"mention_count": "mention_count DESC", "last_seen": "last_seen DESC", "name": "name ASC"}
    order_sql = valid_sorts.get(sort_by, "mention_count DESC")

    with get_db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) as c FROM nodes WHERE {where_sql}", params
        ).fetchone()["c"]

        rows = conn.execute(
            f"""SELECT id, type, name, properties, first_seen, last_seen, mention_count
                FROM nodes WHERE {where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?""",
            params + [limit, offset],
        ).fetchall()

    items = [
        {
            "id": r["id"],
            "type": r["type"],
            "name": r["name"],
            "properties": json.loads(r["properties"]) if r["properties"] else {},
            "first_seen": r["first_seen"],
            "last_seen": r["last_seen"],
            "mention_count": r["mention_count"],
        }
        for r in rows
    ]

    return {"items": items, "total": total, "limit": limit, "offset": offset}


def update_entity(
    entity_id: str,
    name: str | None = None,
    entity_type: str | None = None,
    properties: dict | None = None,
) -> bool:
    """Update an existing entity's fields."""
    updates = []
    params: list[Any] = []

    if name is not None:
        updates.append("name = ?")
        params.append(name.lower().strip())

    if entity_type is not None:
        updates.append("type = ?")
        params.append(entity_type)

    if properties is not None:
        updates.append("properties = ?")
        params.append(json.dumps(properties))

    if not updates:
        return False

    updates.append("last_seen = ?")
    params.append(utc_now())
    params.append(entity_id)

    with get_db() as conn:
        result = conn.execute(
            f"UPDATE nodes SET {', '.join(updates)} WHERE id = ?", params
        )

    if result.rowcount > 0:
        log_audit("entity.updated", {"entity_id": entity_id})
        logger.info("memory.entity_updated", entity_id=entity_id)
        # Reload in-memory graph so name/type changes are visible
        from backend.services.graph_service import reload_graph
        reload_graph()
        return True
    return False


def delete_entity(entity_id: str) -> bool:
    """Delete an entity and all its edges and beliefs."""
    with get_db() as conn:
        # Remove edges
        conn.execute("DELETE FROM edges WHERE source_id = ? OR target_id = ?", (entity_id, entity_id))
        # Remove beliefs
        conn.execute("DELETE FROM beliefs WHERE node_id = ?", (entity_id,))
        # Remove node
        result = conn.execute("DELETE FROM nodes WHERE id = ?", (entity_id,))

    if result.rowcount > 0:
        log_audit("entity.deleted", {"entity_id": entity_id})
        logger.info("memory.entity_deleted", entity_id=entity_id)
        # Reload in-memory graph
        from backend.services.graph_service import reload_graph
        reload_graph()
        return True
    return False


def merge_entities(primary_id: str, secondary_id: str) -> bool:
    """
    Merge two entities: keep primary, transfer secondary's edges/beliefs,
    sum mention counts, then delete secondary.
    """
    with get_db() as conn:
        primary = conn.execute("SELECT * FROM nodes WHERE id = ?", (primary_id,)).fetchone()
        secondary = conn.execute("SELECT * FROM nodes WHERE id = ?", (secondary_id,)).fetchone()

        if not primary or not secondary:
            return False

        # Transfer edges: re-point secondary → primary
        conn.execute(
            "UPDATE edges SET source_id = ? WHERE source_id = ?",
            (primary_id, secondary_id),
        )
        conn.execute(
            "UPDATE edges SET target_id = ? WHERE target_id = ?",
            (primary_id, secondary_id),
        )

        # Transfer beliefs
        conn.execute(
            "UPDATE beliefs SET node_id = ? WHERE node_id = ?",
            (primary_id, secondary_id),
        )

        # Transfer chunk associations via junction table
        conn.execute(
            "INSERT OR IGNORE INTO node_chunks (node_id, chunk_id) "
            "SELECT ?, chunk_id FROM node_chunks WHERE node_id = ?",
            (primary_id, secondary_id),
        )
        conn.execute(
            "DELETE FROM node_chunks WHERE node_id = ?",
            (secondary_id,),
        )

        # Update primary: add mention counts
        conn.execute(
            """UPDATE nodes SET
                mention_count = mention_count + ?,
                last_seen = ?
               WHERE id = ?""",
            (secondary["mention_count"], utc_now(), primary_id),
        )

        # Delete secondary node
        conn.execute("DELETE FROM nodes WHERE id = ?", (secondary_id,))

        # Remove self-edges
        conn.execute(
            "DELETE FROM edges WHERE source_id = target_id AND source_id = ?",
            (primary_id,),
        )

        # Remove duplicate parallel edges that may have been created by the
        # re-pointing above.  Keep the oldest one (MIN id).
        conn.execute(
            """DELETE FROM edges WHERE id NOT IN (
                   SELECT MIN(id) FROM edges
                   GROUP BY source_id, target_id, relationship
               )"""
        )

    log_audit("entity.merged", {"primary": primary_id, "secondary": secondary_id})
    logger.info("memory.entities_merged", primary=primary_id, secondary=secondary_id)

    from backend.services.graph_service import reload_graph
    reload_graph()

    return True


# ---------------------------------------------------------------------------
# Relationship (edge) CRUD
# ---------------------------------------------------------------------------


def get_relationships(
    entity_id: str | None = None,
    relationship_type: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Query relationships with optional filters."""
    where = []
    params: list[Any] = []

    if entity_id:
        where.append("(e.source_id = ? OR e.target_id = ?)")
        params.extend([entity_id, entity_id])

    if relationship_type:
        where.append("e.relationship = ?")
        params.append(relationship_type)

    where_sql = " AND ".join(where) if where else "1=1"

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT e.id, e.source_id, e.target_id, e.relationship, e.properties,
                       e.created_at, e.source_chunk,
                       s.name as source_name, s.type as source_type,
                       t.name as target_name, t.type as target_type
                FROM edges e
                JOIN nodes s ON e.source_id = s.id
                JOIN nodes t ON e.target_id = t.id
                WHERE {where_sql}
                ORDER BY e.created_at DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()

    return [
        {
            "id": r["id"],
            "source": {"id": r["source_id"], "name": r["source_name"], "type": r["source_type"]},
            "target": {"id": r["target_id"], "name": r["target_name"], "type": r["target_type"]},
            "relationship": r["relationship"],
            "properties": json.loads(r["properties"]) if r["properties"] else {},
            "created_at": r["created_at"],
        }
        for r in rows
    ]


def delete_relationship(edge_id: str) -> bool:
    """Delete a specific edge."""
    with get_db() as conn:
        result = conn.execute("DELETE FROM edges WHERE id = ?", (edge_id,))
    if result.rowcount > 0:
        from backend.services.graph_service import reload_graph
        reload_graph()
        return True
    return False


# ---------------------------------------------------------------------------
# Beliefs
# ---------------------------------------------------------------------------


def add_belief(
    entity_id: str,
    belief_text: str,
    confidence: float = 0.8,
    source_chunk_id: str | None = None,
) -> str:
    """Add a belief about an entity. Returns belief ID."""
    belief_id = generate_id()
    now = utc_now()

    with get_db() as conn:
        # Check entity exists
        entity = conn.execute("SELECT id FROM nodes WHERE id = ?", (entity_id,)).fetchone()
        if not entity:
            raise ValueError(f"Entity {entity_id} not found")

        conn.execute(
            """INSERT INTO beliefs (id, node_id, belief, confidence, source_chunk, timestamp)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (belief_id, entity_id, belief_text, confidence, source_chunk_id, now),
        )

    log_audit("belief.added", {"entity_id": entity_id, "belief_id": belief_id})
    return belief_id


def supersede_belief(old_belief_id: str, new_belief_text: str, confidence: float = 0.8) -> str:
    """
    Mark an existing belief as superseded and create a replacement.
    Returns the new belief ID.
    """
    with get_db() as conn:
        old = conn.execute(
            "SELECT node_id FROM beliefs WHERE id = ?", (old_belief_id,)
        ).fetchone()
        if not old:
            raise ValueError(f"Belief {old_belief_id} not found")

        new_id = generate_id()
        now = utc_now()

        conn.execute(
            """INSERT INTO beliefs (id, node_id, belief, confidence, timestamp)
               VALUES (?, ?, ?, ?, ?)""",
            (new_id, old["node_id"], new_belief_text, confidence, now),
        )
        conn.execute(
            "UPDATE beliefs SET superseded_by = ? WHERE id = ?",
            (new_id, old_belief_id),
        )

    log_audit("belief.superseded", {"old": old_belief_id, "new": new_id})
    return new_id


def get_entity_beliefs(entity_id: str, include_superseded: bool = False) -> list[dict]:
    """Get beliefs for an entity."""
    where = "node_id = ?"
    if not include_superseded:
        where += " AND superseded_by IS NULL"

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT id, belief, confidence, source_chunk, timestamp, superseded_by
                FROM beliefs WHERE {where} ORDER BY timestamp DESC""",
            (entity_id,),
        ).fetchall()

    return [
        {
            "id": r["id"],
            "belief": r["belief"],
            "confidence": r["confidence"],
            "source_chunk": r["source_chunk"],
            "timestamp": r["timestamp"],
            "superseded_by": r["superseded_by"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Memory search (full-text across chunks)
# ---------------------------------------------------------------------------


def search_memory(
    query: str,
    modality: str | None = None,
    category: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Full-text search across chunks and documents."""
    where = ["c.content LIKE ?"]
    params: list[Any] = [f"%{query}%"]

    if modality:
        where.append("d.modality = ?")
        params.append(modality)

    if category:
        where.append("c.category = ?")
        params.append(category)

    where_sql = " AND ".join(where)

    with get_db() as conn:
        rows = conn.execute(
            f"""SELECT c.id as chunk_id, c.content, c.chunk_index, c.summary,
                       c.category, c.action_items,
                       d.id as doc_id, d.filename, d.modality, d.ingested_at
                FROM chunks c
                JOIN documents d ON c.document_id = d.id
                WHERE {where_sql}
                ORDER BY d.ingested_at DESC
                LIMIT ?""",
            params + [limit],
        ).fetchall()

    return [
        {
            "chunk_id": r["chunk_id"],
            "content": r["content"][:500],
            "chunk_index": r["chunk_index"],
            "summary": r["summary"],
            "category": r["category"],
            "action_items": json.loads(r["action_items"]) if r["action_items"] else [],
            "document_id": r["doc_id"],
            "filename": r["filename"],
            "modality": r["modality"],
            "ingested_at": r["ingested_at"],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Document ↔ Entity lookups
# ---------------------------------------------------------------------------


def get_document_entities(document_id: str) -> list[dict]:
    """Get all entities mentioned in a document's chunks."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT n.id, n.type, n.name, n.mention_count
               FROM nodes n
               JOIN node_chunks nc ON nc.node_id = n.id
               JOIN chunks c ON c.id = nc.chunk_id
               WHERE c.document_id = ?
               ORDER BY n.mention_count DESC""",
            (document_id,),
        ).fetchall()

    return [
        {"id": r["id"], "type": r["type"], "name": r["name"], "mention_count": r["mention_count"]}
        for r in rows
    ]


def get_entity_documents(entity_id: str) -> list[dict]:
    """Get all documents where an entity was mentioned."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT d.id, d.filename, d.modality, d.ingested_at
                FROM documents d
                JOIN chunks c ON c.document_id = d.id
                JOIN node_chunks nc ON nc.chunk_id = c.id
                WHERE nc.node_id = ?
                ORDER BY d.ingested_at DESC""",
            (entity_id,),
        ).fetchall()

    return [
        {"id": r["id"], "filename": r["filename"], "modality": r["modality"], "ingested_at": r["ingested_at"]}
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Relationship types summary
# ---------------------------------------------------------------------------


def get_relationship_types() -> list[dict]:
    """Get all relationship types with counts."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT relationship, COUNT(*) as count
               FROM edges GROUP BY relationship ORDER BY count DESC"""
        ).fetchall()

    return [{"relationship": r["relationship"], "count": r["count"]} for r in rows]


def get_entity_types() -> list[dict]:
    """Get all entity types with counts."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT type, COUNT(*) as count
               FROM nodes GROUP BY type ORDER BY count DESC"""
        ).fetchall()

    return [{"type": r["type"], "count": r["count"]} for r in rows]
