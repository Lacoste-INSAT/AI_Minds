"""
QdrantStore — Standalone Qdrant vector database wrapper.

Works with any embedding dimension.
"""

import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy imports
_qdrant_models = None


def _load():
    global _qdrant_models
    if _qdrant_models is None:
        from qdrant_client import QdrantClient
        from qdrant_client.models import (
            PointStruct, VectorParams, Distance,
            Filter, FieldCondition, MatchValue,
        )
        _qdrant_models = {
            "QdrantClient": QdrantClient,
            "PointStruct": PointStruct,
            "VectorParams": VectorParams,
            "Distance": Distance,
            "Filter": Filter,
            "FieldCondition": FieldCondition,
            "MatchValue": MatchValue,
        }
    return _qdrant_models


class QdrantStore:
    """Simple Qdrant wrapper for AI MINDS memory."""

    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = "ai_minds_memory",
        dimension: int = 384,
    ):
        q = _load()
        self.collection = collection
        self.client = q["QdrantClient"](url=url)
        self._ensure_collection(dimension)

    def _ensure_collection(self, dimension: int):
        q = _load()
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=q["VectorParams"](
                    size=dimension, distance=q["Distance"].COSINE
                ),
            )
            logger.info(f"Created collection '{self.collection}' (dim={dimension})")

    def upsert(self, vector: list[float], payload: dict, point_id: str = None) -> str:
        """Insert or update a single point. Returns its ID."""
        q = _load()
        pid = point_id or str(uuid.uuid4())
        self.client.upsert(
            collection_name=self.collection,
            points=[q["PointStruct"](id=pid, vector=vector, payload=payload)],
        )
        return pid

    def search(
        self,
        vector: list[float],
        limit: int = 5,
        filters: dict = None,
    ) -> list[dict]:
        """Semantic search. Returns list of {id, score, content, source_file, payload}."""
        q = _load()
        qf = None
        if filters:
            conditions = [
                q["FieldCondition"](key=k, match=q["MatchValue"](value=v))
                for k, v in filters.items() if v is not None
            ]
            if conditions:
                qf = q["Filter"](must=conditions)

        results = self.client.search(
            collection_name=self.collection,
            query_vector=vector,
            limit=limit,
            query_filter=qf,
        )
        return [
            {
                "id": str(r.id),
                "score": round(r.score, 4),
                "content": r.payload.get("content", ""),
                "source_file": r.payload.get("source_file", "unknown"),
                "payload": r.payload,
            }
            for r in results
        ]

    def scroll(self, limit: int = 20, filters: dict = None) -> list[dict]:
        """Browse stored points (no query vector needed)."""
        q = _load()
        qf = None
        if filters:
            conditions = [
                q["FieldCondition"](key=k, match=q["MatchValue"](value=v))
                for k, v in filters.items() if v is not None
            ]
            if conditions:
                qf = q["Filter"](must=conditions)

        points, _ = self.client.scroll(
            collection_name=self.collection,
            limit=limit,
            scroll_filter=qf,
            with_payload=True,
        )
        return [
            {
                "id": str(p.id),
                "content": p.payload.get("content", ""),
                "source_file": p.payload.get("source_file", "unknown"),
                "payload": p.payload,
            }
            for p in points
        ]

    def count(self) -> int:
        return self.client.count(collection_name=self.collection).count

    def delete(self, point_id: str):
        from qdrant_client.models import PointIdsList
        self.client.delete(
            collection_name=self.collection,
            points_selector=PointIdsList(points=[point_id]),
        )
