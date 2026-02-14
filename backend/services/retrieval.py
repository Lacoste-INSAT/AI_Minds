"""
Synapsis Backend — Hybrid Retrieval Service
Dense (Qdrant) + Sparse (BM25) + Graph (NetworkX)
Fusion via Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

import structlog

from backend.config import settings
from backend.database import get_db
from backend.models.schemas import ChunkEvidence

logger = structlog.get_logger(__name__)


@dataclass
class RetrievalResult:
    chunk_id: str
    content: str
    file_name: str
    document_id: str
    score_dense: float = 0.0
    score_sparse: float = 0.0
    score_graph: float = 0.0
    score_final: float = 0.0


# ---------------------------------------------------------------------------
# Dense retrieval (Qdrant)
# ---------------------------------------------------------------------------


def dense_search(query_vector: list[float], top_k: int = 10) -> list[RetrievalResult]:
    """Semantic similarity search via Qdrant."""
    from backend.services.qdrant_service import search_vectors

    results = search_vectors(query_vector, top_k=top_k)
    return [
        RetrievalResult(
            chunk_id=r["payload"].get("chunk_id", r["id"]),
            content=r["payload"].get("content", ""),
            file_name=r["payload"].get("file_name", "unknown"),
            document_id=r["payload"].get("document_id", ""),
            score_dense=r["score"],
        )
        for r in results
    ]


# ---------------------------------------------------------------------------
# Sparse retrieval (BM25)
# ---------------------------------------------------------------------------

_bm25_index = None
_bm25_chunks: list[dict] = []


def build_bm25_index():
    """Build BM25 index from all chunks in SQLite."""
    global _bm25_index, _bm25_chunks

    from rank_bm25 import BM25Okapi

    with get_db() as conn:
        rows = conn.execute(
            """SELECT c.id, c.content, c.document_id, d.filename
               FROM chunks c JOIN documents d ON c.document_id = d.id"""
        ).fetchall()

    if not rows:
        _bm25_index = None
        _bm25_chunks = []
        return

    _bm25_chunks = [
        {
            "chunk_id": r["id"],
            "content": r["content"],
            "document_id": r["document_id"],
            "file_name": r["filename"],
        }
        for r in rows
    ]

    tokenized = [doc["content"].lower().split() for doc in _bm25_chunks]
    _bm25_index = BM25Okapi(tokenized)
    logger.info("bm25.index_built", num_docs=len(_bm25_chunks))


def sparse_search(query: str, top_k: int = 10) -> list[RetrievalResult]:
    """BM25 keyword search."""
    if _bm25_index is None or not _bm25_chunks:
        build_bm25_index()

    if _bm25_index is None:
        return []

    tokenized_query = query.lower().split()
    scores = _bm25_index.get_scores(tokenized_query)

    # Get top-k indices
    indexed_scores = list(enumerate(scores))
    indexed_scores.sort(key=lambda x: x[1], reverse=True)
    top_results = indexed_scores[:top_k]

    results = []
    for idx, score in top_results:
        if score > 0:
            chunk = _bm25_chunks[idx]
            results.append(
                RetrievalResult(
                    chunk_id=chunk["chunk_id"],
                    content=chunk["content"],
                    file_name=chunk["file_name"],
                    document_id=chunk["document_id"],
                    score_sparse=float(score),
                )
            )

    return results


# ---------------------------------------------------------------------------
# Graph retrieval
# ---------------------------------------------------------------------------


def graph_search(query: str, top_k: int = 10) -> list[RetrievalResult]:
    """Find relevant chunks through graph entity traversal."""
    from backend.services.graph_service import get_graph, get_entity_chunks
    from backend.services.entity_extraction import extract_regex, extract_spacy

    # Extract entity names from query
    regex_ents = extract_regex(query)
    spacy_ents = extract_spacy(query)

    entity_names = set()
    for e in regex_ents + spacy_ents:
        entity_names.add(e.name.lower())

    # Also add individual words > 3 chars as potential entity names
    for word in query.split():
        if len(word) > 3:
            entity_names.add(word.lower())

    if not entity_names:
        return []

    # Get chunks associated with entities
    chunk_ids: set[str] = set()
    for name in entity_names:
        cids = get_entity_chunks(name)
        chunk_ids.update(cids)

    if not chunk_ids:
        return []

    # Fetch chunk details from DB
    results = []
    with get_db() as conn:
        for cid in list(chunk_ids)[:top_k]:
            row = conn.execute(
                """SELECT c.id, c.content, c.document_id, d.filename
                   FROM chunks c JOIN documents d ON c.document_id = d.id
                   WHERE c.id = ?""",
                (cid,),
            ).fetchone()
            if row:
                results.append(
                    RetrievalResult(
                        chunk_id=row["id"],
                        content=row["content"],
                        file_name=row["filename"],
                        document_id=row["document_id"],
                        score_graph=1.0,
                    )
                )

    return results


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


def reciprocal_rank_fusion(
    *result_lists: list[RetrievalResult],
    k: int = 60,
    weights: list[float] | None = None,
) -> list[RetrievalResult]:
    """Fuse multiple result lists using Reciprocal Rank Fusion (RRF)."""
    if weights is None:
        weights = [settings.dense_weight, settings.sparse_weight, settings.graph_weight]

    # Ensure weights covers all lists
    while len(weights) < len(result_lists):
        weights.append(1.0 / len(result_lists))

    # Score map
    fused: dict[str, RetrievalResult] = {}
    rrf_scores: dict[str, float] = {}

    for list_idx, results in enumerate(result_lists):
        w = weights[list_idx] if list_idx < len(weights) else 1.0
        for rank, r in enumerate(results):
            rrf_score = w / (k + rank + 1)

            if r.chunk_id not in fused:
                fused[r.chunk_id] = r
                rrf_scores[r.chunk_id] = 0.0

            rrf_scores[r.chunk_id] += rrf_score

            # Merge scores
            existing = fused[r.chunk_id]
            existing.score_dense = max(existing.score_dense, r.score_dense)
            existing.score_sparse = max(existing.score_sparse, r.score_sparse)
            existing.score_graph = max(existing.score_graph, r.score_graph)

    # Set final scores
    for chunk_id, result in fused.items():
        result.score_final = rrf_scores.get(chunk_id, 0.0)

    # Sort by final score
    sorted_results = sorted(fused.values(), key=lambda x: x.score_final, reverse=True)

    return sorted_results


# ---------------------------------------------------------------------------
# Hybrid search (main entry point)
# ---------------------------------------------------------------------------


async def hybrid_search(
    query: str,
    query_vector: list[float],
    top_k: int = 10,
    include_graph: bool = True,
) -> list[RetrievalResult]:
    """
    Run dense + sparse + graph retrieval and fuse results.
    """
    # Dense search
    dense_results = dense_search(query_vector, top_k=top_k)

    # Sparse search
    sparse_results = sparse_search(query, top_k=top_k)

    # Graph search
    graph_results = graph_search(query, top_k=top_k) if include_graph else []

    # Fuse
    fused = reciprocal_rank_fusion(dense_results, sparse_results, graph_results)

    logger.info(
        "retrieval.hybrid_complete",
        dense_count=len(dense_results),
        sparse_count=len(sparse_results),
        graph_count=len(graph_results),
        fused_count=len(fused),
    )

    return fused[:top_k]


def results_to_evidence(results: list[RetrievalResult]) -> list[ChunkEvidence]:
    """Convert retrieval results to ChunkEvidence for API response."""
    return [
        ChunkEvidence(
            chunk_id=r.chunk_id,
            file_name=r.file_name,
            snippet=r.content[:500],
            score_dense=r.score_dense,
            score_sparse=r.score_sparse,
            score_final=r.score_final,
        )
        for r in results
    ]
