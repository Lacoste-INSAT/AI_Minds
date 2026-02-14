"""
Synapsis Backend — Memory Router
GET /memory/graph — graph data for visualization
GET /memory/timeline — chronological feed
GET /memory/{id} — single knowledge card
GET /memory/stats — counts, categories, entities
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
import structlog

from backend.database import get_db
from backend.models.schemas import (
    GraphData,
    GraphNode,
    GraphEdge,
    TimelineResponse,
    TimelineItem,
    MemoryDetail,
    MemoryStats,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/graph", response_model=GraphData)
async def get_graph(
    limit: int = Query(200, ge=1, le=1000, description="Max nodes to return"),
):
    """Return graph data (nodes + edges) for frontend visualization."""
    from backend.services.graph_service import get_graph_data

    data = get_graph_data(limit=limit)

    nodes = [GraphNode(**n) for n in data["nodes"]]
    edges = [GraphEdge(**e) for e in data["edges"]]

    return GraphData(nodes=nodes, edges=edges)


@router.get("/timeline", response_model=TimelineResponse)
async def get_timeline(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="Filter by category"),
    modality: Optional[str] = Query(None, description="Filter by modality"),
    search: Optional[str] = Query(None, description="Search in content"),
    sort: str = Query("desc", pattern="^(asc|desc)$"),
):
    """Return memories sorted by date with filters."""
    offset = (page - 1) * page_size

    with get_db() as conn:
        # Build query dynamically
        where_clauses = ["d.status = 'processed'"]
        params: list = []

        if category:
            where_clauses.append("c.category = ?")
            params.append(category)

        if modality:
            where_clauses.append("d.modality = ?")
            params.append(modality)

        if search:
            where_clauses.append("c.content LIKE ?")
            params.append(f"%{search}%")

        where_sql = " AND ".join(where_clauses)
        order = "DESC" if sort == "desc" else "ASC"

        # Get total count
        count_sql = f"""
            SELECT COUNT(DISTINCT d.id) as total
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            WHERE {where_sql}
        """
        total = conn.execute(count_sql, params).fetchone()["total"]

        # Get page
        query_sql = f"""
            SELECT DISTINCT d.id, d.filename, d.modality, d.source_uri, d.ingested_at,
                   MIN(c.summary) as summary, MIN(c.category) as category
            FROM documents d
            LEFT JOIN chunks c ON c.document_id = d.id
            WHERE {where_sql}
            GROUP BY d.id
            ORDER BY d.ingested_at {order}
            LIMIT ? OFFSET ?
        """
        params.extend([page_size, offset])
        rows = conn.execute(query_sql, params).fetchall()

    items = []
    for row in rows:
        # Get entities for this document
        entities = _get_document_entities(row["id"])

        items.append(
            TimelineItem(
                id=row["id"],
                title=row["filename"],
                summary=row["summary"],
                category=row["category"],
                modality=row["modality"],
                source_uri=row["source_uri"],
                ingested_at=row["ingested_at"],
                entities=entities,
            )
        )

    return TimelineResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=MemoryStats)
async def get_stats():
    """Return memory statistics."""
    with get_db() as conn:
        docs = conn.execute("SELECT COUNT(*) as c FROM documents WHERE status = 'processed'").fetchone()["c"]
        chunks = conn.execute("SELECT COUNT(*) as c FROM chunks").fetchone()["c"]
        nodes = conn.execute("SELECT COUNT(*) as c FROM nodes").fetchone()["c"]
        edges = conn.execute("SELECT COUNT(*) as c FROM edges").fetchone()["c"]

        # Categories
        cat_rows = conn.execute(
            "SELECT category, COUNT(*) as c FROM chunks WHERE category IS NOT NULL GROUP BY category"
        ).fetchall()
        categories = {r["category"]: r["c"] for r in cat_rows}

        # Modalities
        mod_rows = conn.execute(
            "SELECT modality, COUNT(*) as c FROM documents GROUP BY modality"
        ).fetchall()
        modalities = {r["modality"]: r["c"] for r in mod_rows}

        # Entity types
        type_rows = conn.execute(
            "SELECT type, COUNT(*) as c FROM nodes GROUP BY type"
        ).fetchall()
        entity_types = {r["type"]: r["c"] for r in type_rows}

    return MemoryStats(
        total_documents=docs,
        total_chunks=chunks,
        total_nodes=nodes,
        total_edges=edges,
        categories=categories,
        modalities=modalities,
        entity_types=entity_types,
    )


@router.get("/{memory_id}", response_model=MemoryDetail)
async def get_memory_detail(memory_id: str):
    """Get full detail for a single memory/document."""
    with get_db() as conn:
        doc = conn.execute(
            "SELECT * FROM documents WHERE id = ?", (memory_id,)
        ).fetchone()

        if not doc:
            raise HTTPException(status_code=404, detail="Memory not found")

        chunks = conn.execute(
            "SELECT id, content, chunk_index, summary, category, action_items FROM chunks WHERE document_id = ? ORDER BY chunk_index",
            (memory_id,),
        ).fetchall()

    chunk_list = []
    entities_set = set()
    action_items_all = []
    summary = None
    category = None

    for chunk in chunks:
        chunk_dict = {
            "id": chunk["id"],
            "content": chunk["content"],
            "chunk_index": chunk["chunk_index"],
        }
        if chunk["summary"]:
            summary = chunk["summary"]
        if chunk["category"]:
            category = chunk["category"]
        if chunk["action_items"]:
            try:
                items = json.loads(chunk["action_items"])
                action_items_all.extend(items)
            except (json.JSONDecodeError, TypeError):
                pass
        chunk_list.append(chunk_dict)

    entities = _get_document_entities(memory_id)

    return MemoryDetail(
        id=doc["id"],
        filename=doc["filename"],
        modality=doc["modality"],
        source_uri=doc["source_uri"],
        ingested_at=doc["ingested_at"],
        status=doc["status"],
        summary=summary,
        category=category,
        entities=entities,
        action_items=action_items_all,
        chunks=chunk_list,
    )


def _get_document_entities(document_id: str) -> list[str]:
    """Get entity names associated with a document's chunks."""
    with get_db() as conn:
        # Single query: join chunks → nodes via source_chunks LIKE match
        rows = conn.execute(
            """SELECT DISTINCT n.name
               FROM nodes n
               JOIN chunks c ON c.document_id = ?
               WHERE n.source_chunks LIKE '%' || c.id || '%'""",
            (document_id,),
        ).fetchall()
    return [r["name"] for r in rows]
