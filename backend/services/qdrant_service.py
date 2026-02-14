"""
Synapsis Backend — Qdrant Vector Store Service
Manages vector storage and similarity search.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)

_client = None


def _get_client():
    """Lazy-load Qdrant client."""
    global _client
    if _client is None:
        from qdrant_client import QdrantClient

        _client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
        logger.info("qdrant.connected", host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def ensure_collection():
    """Create the collection if it doesn't exist."""
    from qdrant_client.models import Distance, VectorParams

    client = _get_client()
    collections = [c.name for c in client.get_collections().collections]
    if settings.qdrant_collection not in collections:
        client.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(
                size=settings.embedding_dim,
                distance=Distance.COSINE,
            ),
        )
        logger.info("qdrant.collection_created", name=settings.qdrant_collection)
    else:
        logger.info("qdrant.collection_exists", name=settings.qdrant_collection)


def upsert_vectors(
    ids: list[str],
    vectors: list[list[float]],
    payloads: list[dict[str, Any]],
):
    """Upsert vectors with payloads into the collection."""
    from qdrant_client.models import PointStruct

    client = _get_client()
    points = [
        PointStruct(
            id=uid,
            vector=vec,
            payload=payload,
        )
        for uid, vec, payload in zip(ids, vectors, payloads)
    ]
    client.upsert(
        collection_name=settings.qdrant_collection,
        points=points,
    )
    logger.debug("qdrant.upserted", count=len(points))


def search_vectors(
    query_vector: list[float],
    top_k: int = 10,
    score_threshold: float | None = None,
    filters: dict | None = None,
) -> list[dict]:
    """Search for similar vectors. Returns list of {id, score, payload}."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()

    qdrant_filter = None
    if filters:
        conditions = []
        for key, value in filters.items():
            conditions.append(
                FieldCondition(key=key, match=MatchValue(value=value))
            )
        qdrant_filter = Filter(must=conditions)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
    )

    return [
        {
            "id": str(r.id),
            "score": r.score,
            "payload": r.payload or {},
        }
        for r in results
    ]


def get_collection_info() -> dict:
    """Get collection stats."""
    try:
        client = _get_client()
        info = client.get_collection(settings.qdrant_collection)
        return {
            "status": "up",
            "vectors_count": info.vectors_count or 0,
            "points_count": info.points_count or 0,
        }
    except Exception as e:
        logger.error("qdrant.info_failed", error=str(e))
        return {"status": "down", "error": str(e)}


def delete_by_document_id(document_id: str):
    """Delete all vectors associated with a document."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue, FilterSelector

    client = _get_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=FilterSelector(
            filter=Filter(
                must=[
                    FieldCondition(
                        key="document_id",
                        match=MatchValue(value=document_id),
                    )
                ]
            )
        ),
    )
    logger.debug("qdrant.deleted_by_document", document_id=document_id)


def is_available() -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = _get_client()
        client.get_collections()
        return True
    except Exception:
        return False
