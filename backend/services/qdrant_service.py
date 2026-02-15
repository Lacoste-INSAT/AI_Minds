"""
Synapsis Backend — Qdrant Vector Store Service
Manages vector storage and similarity search.

Uses qdrant-client to communicate with a Qdrant instance (Docker).
Collection: ``synapsis_chunks`` — 384-dim cosine, payload-indexed on
``document_id``, ``file_name``, ``modality``.
"""

from __future__ import annotations

import uuid
from typing import Any

import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_BATCH_SIZE = 64  # Max points per upsert batch (keeps gRPC frame small)

# Payload fields to create keyword indexes on
_INDEXED_FIELDS: list[tuple[str, str]] = [
    ("document_id", "keyword"),
    ("file_name", "keyword"),
    ("modality", "keyword"),
]

# ---------------------------------------------------------------------------
# Client singleton
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    """Lazy-load Qdrant client with automatic reconnection."""
    global _client
    if _client is None:
        from qdrant_client import QdrantClient

        _client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            timeout=30,
            prefer_grpc=False,
        )
        logger.info(
            "qdrant.connected",
            host=settings.qdrant_host,
            port=settings.qdrant_port,
        )
    return _client


def reset_client() -> None:
    """Force-close and reset the client (useful after connection errors)."""
    global _client
    if _client is not None:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    logger.info("qdrant.client_reset")


# ---------------------------------------------------------------------------
# Collection management
# ---------------------------------------------------------------------------


def ensure_collection() -> None:
    """
    Create the collection if it doesn't exist, then ensure payload indexes.
    Called once at application startup.
    """
    from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

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

    # Ensure payload indexes for fast filtered search
    _ensure_payload_indexes(client)


def _ensure_payload_indexes(client) -> None:
    """Create keyword indexes on common filter fields if missing."""
    from qdrant_client.models import PayloadSchemaType

    schema_map = {
        "keyword": PayloadSchemaType.KEYWORD,
        "integer": PayloadSchemaType.INTEGER,
        "float": PayloadSchemaType.FLOAT,
    }

    for field_name, field_type in _INDEXED_FIELDS:
        try:
            client.create_payload_index(
                collection_name=settings.qdrant_collection,
                field_name=field_name,
                field_schema=schema_map[field_type],
            )
            logger.debug("qdrant.index_created", field=field_name)
        except Exception:
            # Index already exists — safe to ignore
            pass


def recreate_collection() -> None:
    """Drop and re-create the collection (destructive — use for resets)."""
    from qdrant_client.models import Distance, VectorParams

    client = _get_client()
    client.recreate_collection(
        collection_name=settings.qdrant_collection,
        vectors_config=VectorParams(
            size=settings.embedding_dim,
            distance=Distance.COSINE,
        ),
    )
    _ensure_payload_indexes(client)
    logger.info("qdrant.collection_recreated", name=settings.qdrant_collection)


# ---------------------------------------------------------------------------
# Upsert
# ---------------------------------------------------------------------------


def _str_to_uuid(s: str) -> str:
    """
    Convert an arbitrary string ID to a deterministic UUID-5 string.
    Qdrant accepts UUIDs or unsigned ints as point IDs.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


def upsert_vectors(
    ids: list[str],
    vectors: list[list[float]],
    payloads: list[dict[str, Any]],
) -> int:
    """
    Upsert vectors with payloads into the collection.

    IDs are converted to deterministic UUID-5 so Qdrant accepts them.
    Large batches are chunked into groups of ``_BATCH_SIZE``.
    The original string ID is stored in the payload as ``_original_id``.

    Returns the number of points upserted.
    """
    from qdrant_client.models import PointStruct

    if not (len(ids) == len(vectors) == len(payloads)):
        raise ValueError(
            f"Input list lengths must match: ids={len(ids)}, "
            f"vectors={len(vectors)}, payloads={len(payloads)}"
        )

    if not ids:
        return 0

    client = _get_client()
    total = 0

    for batch_start in range(0, len(ids), _BATCH_SIZE):
        batch_end = min(batch_start + _BATCH_SIZE, len(ids))
        points = []

        for i in range(batch_start, batch_end):
            payload = {**payloads[i], "_original_id": ids[i]}
            points.append(
                PointStruct(
                    id=_str_to_uuid(ids[i]),
                    vector=vectors[i],
                    payload=payload,
                )
            )

        client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
            wait=True,
        )
        total += len(points)

    logger.debug("qdrant.upserted", count=total)
    return total


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


def search_vectors(
    query_vector: list[float],
    top_k: int = 10,
    score_threshold: float | None = None,
    filters: dict | None = None,
) -> list[dict]:
    """
    Semantic similarity search via Qdrant.

    Uses ``client.search`` (qdrant-client 1.x compatible).

    Parameters
    ----------
    query_vector : 384-dim embedding
    top_k : max results
    score_threshold : optional minimum cosine similarity
    filters : optional ``{field: value}`` exact-match filter dict

    Returns list of ``{"id", "score", "payload"}`` dicts.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    results = client.search(
        collection_name=settings.qdrant_collection,
        query_vector=query_vector,
        limit=top_k,
        score_threshold=score_threshold,
        query_filter=qdrant_filter,
        with_payload=True,
    )

    return [
        {
            "id": str(r.id),
            "score": r.score,
            "payload": r.payload or {},
        }
        for r in results
    ]


def search_by_document(
    query_vector: list[float],
    document_id: str,
    top_k: int = 5,
) -> list[dict]:
    """Search within a specific document's chunks."""
    return search_vectors(
        query_vector=query_vector,
        top_k=top_k,
        filters={"document_id": document_id},
    )


# ---------------------------------------------------------------------------
# Scroll / list all points
# ---------------------------------------------------------------------------


def scroll_all(
    limit: int = 100,
    offset: str | None = None,
    filters: dict | None = None,
    with_vectors: bool = False,
) -> tuple[list[dict], str | None]:
    """
    Paginate through all points in the collection.

    Returns ``(points, next_offset)`` — pass ``next_offset`` back as
    ``offset`` to fetch the next page.  ``None`` means end of data.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    records, next_offset = client.scroll(
        collection_name=settings.qdrant_collection,
        limit=limit,
        offset=offset,
        scroll_filter=qdrant_filter,
        with_payload=True,
        with_vectors=with_vectors,
    )

    points = [
        {
            "id": str(r.id),
            "payload": r.payload or {},
            "vector": r.vector if with_vectors else None,
        }
        for r in records
    ]

    return points, str(next_offset) if next_offset else None


def count_points(filters: dict | None = None) -> int:
    """Count points in the collection, optionally filtered."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()

    qdrant_filter = None
    if filters:
        conditions = [
            FieldCondition(key=key, match=MatchValue(value=value))
            for key, value in filters.items()
        ]
        qdrant_filter = Filter(must=conditions)

    result = client.count(
        collection_name=settings.qdrant_collection,
        count_filter=qdrant_filter,
        exact=True,
    )
    return result.count


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


def delete_by_document_id(document_id: str) -> None:
    """Delete all vectors associated with a document."""
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = _get_client()
    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        ),
    )
    logger.debug("qdrant.deleted_by_document", document_id=document_id)


def delete_by_ids(chunk_ids: list[str]) -> None:
    """Delete specific points by their original string IDs."""
    from qdrant_client.models import PointIdsList

    if not chunk_ids:
        return

    client = _get_client()
    uuid_ids = [_str_to_uuid(cid) for cid in chunk_ids]

    client.delete(
        collection_name=settings.qdrant_collection,
        points_selector=PointIdsList(points=uuid_ids),
    )
    logger.debug("qdrant.deleted_by_ids", count=len(uuid_ids))


# ---------------------------------------------------------------------------
# Info / health
# ---------------------------------------------------------------------------


def get_collection_info() -> dict:
    """Get collection statistics for health checks."""
    try:
        client = _get_client()
        info = client.get_collection(settings.qdrant_collection)
        return {
            "status": "up",
            "vectors_count": getattr(info, "indexed_vectors_count", 0) or 0,
            "points_count": info.points_count or 0,
        }
    except Exception as e:
        logger.error("qdrant.info_failed", error=str(e))
        return {
            "status": "down",
            "vectors_count": 0,
            "points_count": 0,
        }


def is_available() -> bool:
    """Check if Qdrant is reachable."""
    try:
        client = _get_client()
        client.get_collections()
        return True
    except Exception:
        return False
