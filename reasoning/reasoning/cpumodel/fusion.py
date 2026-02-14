"""
Synapsis Reasoning Engine - RRF Fusion
Reciprocal Rank Fusion to merge results from dense, sparse, and graph retrieval.

RRF Formula: score(d) = Σ 1 / (k + rank_i(d))
where k is a constant (typically 60) and rank_i is the rank of document d in list i.

After fusion, results are reranked by: relevance × recency
"""
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Optional

from .models import ChunkEvidence, RetrievalResult, FusedContext


logger = logging.getLogger(__name__)

# RRF constant - controls how much rank matters vs presence in list
RRF_K = 60

# Weight for recency in final score (0 = ignore recency, 1 = only recency)
RECENCY_WEIGHT = 0.2


def _compute_rrf_score(ranks: list[int], k: int = RRF_K) -> float:
    """
    Compute RRF score from ranks in multiple lists.
    Higher score = better (more lists, higher ranks).
    """
    if not ranks:
        return 0.0
    return sum(1.0 / (k + r) for r in ranks)


def _compute_recency_factor(timestamp: Optional[str]) -> float:
    """
    Compute recency factor (0-1) based on document timestamp.
    More recent = higher factor.
    Uses exponential decay with 30-day half-life.
    """
    if not timestamp:
        return 0.5  # Neutral if unknown
    
    try:
        # Parse timestamp (assumes ISO format)
        doc_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(doc_time.tzinfo) if doc_time.tzinfo else datetime.now()
        
        age_days = (now - doc_time).days
        
        # Exponential decay: 0.5 at 30 days, ~0 at 90+ days
        half_life_days = 30
        factor = 0.5 ** (age_days / half_life_days)
        
        return min(1.0, max(0.0, factor))
        
    except Exception:
        return 0.5


def fuse_results(
    retrieval_results: dict[str, RetrievalResult],
    top_k: int = 10,
    apply_recency: bool = True,
) -> FusedContext:
    """
    Merge results from multiple retrieval paths using RRF.
    
    Steps:
    1. Collect all chunks from all paths
    2. Compute RRF score for each chunk
    3. Deduplicate by chunk_id (keep highest score)
    4. Apply recency weighting (optional)
    5. Sort by final score and return top-k
    """
    start_time = time.perf_counter()
    
    # Step 1: Build rank maps for each retrieval type
    # chunk_id -> list of (retrieval_type, rank, original_score)
    chunk_ranks: dict[str, list[tuple[str, int, float]]] = defaultdict(list)
    chunk_data: dict[str, ChunkEvidence] = {}
    
    counts = {"dense": 0, "sparse": 0, "graph": 0}
    
    for retrieval_type, result in retrieval_results.items():
        for rank, chunk in enumerate(result.chunks, start=1):
            chunk_id = chunk.chunk_id
            
            # Get the relevant score for this retrieval type
            if retrieval_type == "dense":
                original_score = chunk.score_dense
            elif retrieval_type == "sparse":
                original_score = chunk.score_sparse
            else:
                original_score = chunk.score_graph
            
            chunk_ranks[chunk_id].append((retrieval_type, rank, original_score))
            
            # Keep the chunk with most info (prefer one with snippet)
            if chunk_id not in chunk_data or len(chunk.snippet) > len(chunk_data[chunk_id].snippet):
                chunk_data[chunk_id] = chunk
            
            counts[retrieval_type] = counts.get(retrieval_type, 0) + 1
    
    # Step 2: Compute RRF scores
    rrf_scores: dict[str, float] = {}
    for chunk_id, rank_list in chunk_ranks.items():
        ranks = [r[1] for r in rank_list]
        rrf_scores[chunk_id] = _compute_rrf_score(ranks)
    
    # Step 3: Build fused chunks with combined scores
    fused_chunks = []
    for chunk_id, rrf_score in rrf_scores.items():
        chunk = chunk_data[chunk_id]
        
        # Collect individual scores
        for retrieval_type, rank, original_score in chunk_ranks[chunk_id]:
            if retrieval_type == "dense":
                chunk.score_dense = original_score
            elif retrieval_type == "sparse":
                chunk.score_sparse = original_score
            else:
                chunk.score_graph = original_score
        
        # Compute final score
        relevance_score = rrf_score
        
        # Apply recency weighting if enabled
        # Note: Would need timestamp from chunk metadata
        # Using neutral factor (0.5) consistent with _compute_recency_factor
        # to avoid inflating scores until timestamps are available
        recency_factor = 0.5  # TODO: Get timestamp from chunk metadata
        
        if apply_recency:
            final_score = (1 - RECENCY_WEIGHT) * relevance_score + RECENCY_WEIGHT * recency_factor
        else:
            final_score = relevance_score
        
        chunk.score_final = final_score
        fused_chunks.append(chunk)
    
    # Step 4: Sort by final score and take top-k
    fused_chunks.sort(key=lambda c: c.score_final, reverse=True)
    top_chunks = fused_chunks[:top_k]
    
    latency = (time.perf_counter() - start_time) * 1000
    
    logger.info(
        f"RRF fusion: {len(chunk_data)} unique chunks from "
        f"D:{counts['dense']} S:{counts['sparse']} G:{counts.get('graph', 0)} -> top {len(top_chunks)} in {latency:.1f}ms"
    )
    
    return FusedContext(
        chunks=top_chunks,
        dense_count=counts["dense"],
        sparse_count=counts["sparse"],
        graph_count=counts.get("graph", 0),
        fusion_latency_ms=latency,
    )


def format_context_for_llm(fused: FusedContext, max_chars: int = 4000) -> str:
    """
    Format fused chunks into a context string for LLM reasoning.
    Includes source markers for citation.
    """
    if not fused.chunks:
        return "[No relevant context found]"
    
    parts = []
    total_chars = 0
    
    for i, chunk in enumerate(fused.chunks, start=1):
        source_marker = f"[Source {i}]"
        file_info = f" ({chunk.file_name})" if chunk.file_name else ""
        page_info = f" p.{chunk.page_number}" if chunk.page_number else ""
        
        header = f"{source_marker}{file_info}{page_info}:"
        content = chunk.snippet.strip()
        
        entry = f"{header}\n{content}\n"
        
        if total_chars + len(entry) > max_chars:
            break
        
        parts.append(entry)
        total_chars += len(entry)
    
    return "\n".join(parts)
