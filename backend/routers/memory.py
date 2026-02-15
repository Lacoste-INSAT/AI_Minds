"""
Synapsis Backend — Memory Router

Entity / Graph / Structured-DB endpoints:
  GET    /memory/graph           — graph data for visualization
  GET    /memory/graph/stats     — graph analytics (density, components, degrees)
  GET    /memory/graph/centrality — centrality metrics (degree, betweenness, pagerank)
  GET    /memory/graph/communities — community detection
  GET    /memory/graph/subgraph  — extract subgraph for given entity names
  GET    /memory/entities        — search / list entities
  GET    /memory/entities/{id}   — single entity with edges + beliefs
  PATCH  /memory/entities/{id}   — update entity fields
  DELETE /memory/entities/{id}   — delete entity and its edges/beliefs
  POST   /memory/entities/merge  — merge two entities
  GET    /memory/entities/{id}/similar — similar entities (Jaccard)
  GET    /memory/entities/{id}/beliefs — beliefs about an entity
  POST   /memory/entities/{id}/beliefs — add a belief
  GET    /memory/relationships   — query relationships
  DELETE /memory/relationships/{id} — delete a relationship
  GET    /memory/timeline        — chronological feed
  GET    /memory/stats           — counts, categories, entities
  GET    /memory/search          — full-text search across chunks
  GET    /memory/{id}            — single knowledge card
"""

from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Query, HTTPException, Body
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
from backend.services import graph_service, memory_service

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/graph", response_model=GraphData)
async def get_graph(
    limit: int = Query(200, ge=1, le=1000, description="Max nodes to return"),
):
    """Return graph data (nodes + edges) for frontend visualization."""
    data = graph_service.get_graph_data(limit=limit)

    nodes = [GraphNode(**n) for n in data["nodes"]]
    edges = [GraphEdge(**e) for e in data["edges"]]

    return GraphData(nodes=nodes, edges=edges)


# ---------------------------------------------------------------------------
# Graph analytics endpoints
# ---------------------------------------------------------------------------


@router.get("/graph/stats")
async def get_graph_stats_endpoint():
    """Graph statistics: density, components, degree distribution, type counts."""
    return graph_service.get_graph_stats()


@router.get("/graph/centrality")
async def get_centrality(
    top_k: int = Query(20, ge=1, le=100),
):
    """Centrality metrics: degree, betweenness, PageRank."""
    return graph_service.get_centrality_metrics(top_k=top_k)


@router.get("/graph/communities")
async def get_communities():
    """Community detection using label propagation."""
    communities = graph_service.detect_communities()
    return {"communities": communities, "count": len(communities)}


@router.get("/graph/subgraph")
async def get_subgraph(
    entities: str = Query(..., description="Comma-separated entity names"),
    depth: int = Query(1, ge=0, le=3),
):
    """Extract subgraph around the given entity names."""
    names = [n.strip() for n in entities.split(",") if n.strip()]
    return graph_service.get_subgraph_for_entities(names, max_depth=depth)


# ---------------------------------------------------------------------------
# Entity CRUD endpoints
# ---------------------------------------------------------------------------


@router.get("/entities")
async def list_entities(
    q: Optional[str] = Query(None, description="Search query for entity names"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("mention_count", pattern="^(mention_count|last_seen|name)$"),
):
    """Search and list entities with filters."""
    return memory_service.search_entities(query=q, entity_type=entity_type, limit=limit, offset=offset, sort_by=sort_by)


@router.get("/entities/{entity_id}")
async def get_entity_detail(entity_id: str):
    """Get a single entity with its relationships and beliefs."""
    entity = memory_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return entity


@router.patch("/entities/{entity_id}")
async def update_entity_endpoint(
    entity_id: str,
    name: Optional[str] = Body(None),
    entity_type: Optional[str] = Body(None),
    properties: Optional[dict] = Body(None),
):
    """Update an entity's fields."""
    success = memory_service.update_entity(entity_id, name=name, entity_type=entity_type, properties=properties)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found or nothing to update")
    return {"status": "updated", "entity_id": entity_id}


@router.delete("/entities/{entity_id}")
async def delete_entity_endpoint(entity_id: str):
    """Delete an entity and all its edges / beliefs."""
    success = memory_service.delete_entity(entity_id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "deleted", "entity_id": entity_id}


@router.post("/entities/merge")
async def merge_entities_endpoint(
    primary_id: str = Body(..., description="ID of the entity to keep"),
    secondary_id: str = Body(..., description="ID of the entity to merge into primary"),
):
    """Merge two entities: keep primary, transfer secondary's edges & beliefs."""
    success = memory_service.merge_entities(primary_id, secondary_id)
    if not success:
        raise HTTPException(status_code=404, detail="One or both entities not found")
    return {"status": "merged", "primary_id": primary_id}


@router.get("/entities/{entity_id}/similar")
async def get_similar_entities(
    entity_id: str,
    top_k: int = Query(10, ge=1, le=50),
):
    """Find similar entities based on Jaccard neighborhood similarity."""
    entity = memory_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return graph_service.get_entity_similarity(entity["name"], top_k=top_k)


@router.get("/entities/{entity_id}/beliefs")
async def list_beliefs(
    entity_id: str,
    include_superseded: bool = Query(False),
):
    """Get beliefs about an entity."""
    return memory_service.get_entity_beliefs(entity_id, include_superseded=include_superseded)


@router.post("/entities/{entity_id}/beliefs")
async def add_belief_endpoint(
    entity_id: str,
    belief: str = Body(...),
    confidence: float = Body(0.8, ge=0.0, le=1.0),
):
    """Add a belief about an entity."""
    try:
        belief_id = memory_service.add_belief(entity_id, belief, confidence)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"status": "created", "belief_id": belief_id}


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


@router.get("/relationships")
async def list_relationships(
    entity_id: Optional[str] = Query(None),
    relationship_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    """Query relationships with optional entity or type filter."""
    return memory_service.get_relationships(entity_id=entity_id, relationship_type=relationship_type, limit=limit)


@router.delete("/relationships/{edge_id}")
async def delete_relationship_endpoint(edge_id: str):
    """Delete a relationship."""
    success = memory_service.delete_relationship(edge_id)
    if not success:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return {"status": "deleted", "edge_id": edge_id}


# ---------------------------------------------------------------------------
# Full-text memory search
# ---------------------------------------------------------------------------


@router.get("/search")
async def search_memory_endpoint(
    q: str = Query(..., min_length=1, description="Search query"),
    modality: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
):
    """Full-text search across all chunks."""
    return memory_service.search_memory(query=q, modality=modality, category=category, limit=limit)


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

    # Batch-fetch entities for all documents on this page (avoids N+1)
    doc_ids = [row["id"] for row in rows]
    entities_by_doc: dict[str, list[str]] = {did: [] for did in doc_ids}
    if doc_ids:
        placeholders = ", ".join("?" * len(doc_ids))
        with get_db() as conn:
            ent_rows = conn.execute(
                f"""SELECT DISTINCT c.document_id, n.name
                    FROM nodes n
                    JOIN node_chunks nc ON nc.node_id = n.id
                    JOIN chunks c ON c.id = nc.chunk_id
                    WHERE c.document_id IN ({placeholders})""",
                doc_ids,
            ).fetchall()
        for er in ent_rows:
            entities_by_doc[er["document_id"]].append(er["name"])

    items = []
    for row in rows:
        items.append(
            TimelineItem(
                id=row["id"],
                title=row["filename"],
                summary=row["summary"],
                category=row["category"],
                modality=row["modality"],
                source_uri=row["source_uri"],
                ingested_at=row["ingested_at"],
                entities=entities_by_doc.get(row["id"], []),
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
    """Get entity names associated with a document's chunks via junction table."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT DISTINCT n.name
               FROM nodes n
               JOIN node_chunks nc ON nc.node_id = n.id
               JOIN chunks c ON c.id = nc.chunk_id
               WHERE c.document_id = ?""",
            (document_id,),
        ).fetchall()
    return [r["name"] for r in rows]
