"""
RRF Fusion (Reciprocal Rank Fusion)
===================================
Merges results from multiple retrieval paths into a single ranked list.

RRF Formula: score(d) = Σ 1/(k + rank(d))
Where k is a constant (typically 60) and rank is the position in each list.

Why RRF:
- Simple, effective, no hyperparameters to tune
- Works well even when scores from different retrievers aren't comparable
- Rewards items that appear in multiple lists
"""

import structlog
from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from .retriever import RetrievalResult, RetrievalBundle

logger = structlog.get_logger(__name__)


@dataclass
class FusedResult:
    """Result after fusion with combined score."""
    chunk_id: str
    content: str
    source_file: str
    fused_score: float
    retrieval_paths: list[str]  # Which paths found this
    path_scores: dict[str, float]  # Score from each path
    path_ranks: dict[str, int]  # Rank in each path
    metadata: dict
    
    @property
    def citation_label(self) -> str:
        filename = self.source_file.split("/")[-1].split("\\")[-1]
        return filename[:30] + "..." if len(filename) > 30 else filename
    
    @property
    def found_by_multiple(self) -> bool:
        """True if found by more than one retrieval path."""
        return len(self.retrieval_paths) > 1


class RRFFusion:
    """
    Reciprocal Rank Fusion to merge retrieval results.
    
    Features:
    - Standard RRF merging
    - Optional recency weighting
    - Deduplication by chunk_id
    - Source tracking (which paths found each result)
    
    Usage:
        fusion = RRFFusion(k=60, recency_weight=0.2)
        fused = fusion.fuse(retrieval_bundle, top_k=10)
    """
    
    def __init__(
        self,
        k: int = 60,
        recency_weight: float = 0.0,
        recency_halflife_days: int = 30,
    ):
        """
        Args:
            k: RRF constant (higher = less emphasis on top ranks)
            recency_weight: Weight for recency factor (0-1)
            recency_halflife_days: Days until recency factor is 0.5
        """
        self.k = k
        self.recency_weight = recency_weight
        self.recency_halflife_days = recency_halflife_days
    
    def fuse(
        self,
        bundle: RetrievalBundle,
        top_k: int = 10,
        temporal_sort: bool = False,
    ) -> list[FusedResult]:
        """
        Fuse results from all retrieval paths.
        
        Args:
            bundle: RetrievalBundle from HybridRetriever
            top_k: Number of final results to return
            temporal_sort: If True, sort by time instead of relevance
            
        Returns:
            List of FusedResult sorted by combined score
        """
        # Collect all results by chunk_id
        chunk_data: dict[str, dict] = {}
        chunk_ranks: dict[str, dict[str, int]] = defaultdict(dict)
        chunk_scores: dict[str, dict[str, float]] = defaultdict(dict)
        
        # Process each path's results
        for path_name, results in [
            ("dense", bundle.dense_results),
            ("sparse", bundle.sparse_results),
            ("graph", bundle.graph_results),
        ]:
            for rank, result in enumerate(results, start=1):
                cid = result.chunk_id
                
                # Store the result data (use first occurrence)
                if cid not in chunk_data:
                    chunk_data[cid] = {
                        "content": result.content,
                        "source_file": result.source_file,
                        "metadata": result.metadata,
                        "paths": [],
                    }
                
                # Track which paths found this result
                chunk_data[cid]["paths"].append(path_name)
                chunk_ranks[cid][path_name] = rank
                chunk_scores[cid][path_name] = result.score
        
        # Calculate RRF scores
        fused_results = []
        
        for chunk_id, data in chunk_data.items():
            # RRF score: sum of 1/(k + rank) for each path that found it
            rrf_score = 0.0
            for path, rank in chunk_ranks[chunk_id].items():
                rrf_score += 1.0 / (self.k + rank)
            
            # Optional recency weighting
            final_score = rrf_score
            if self.recency_weight > 0:
                recency_factor = self._calculate_recency(data["metadata"])
                final_score = (1 - self.recency_weight) * rrf_score + self.recency_weight * recency_factor
            
            fused_results.append(FusedResult(
                chunk_id=chunk_id,
                content=data["content"],
                source_file=data["source_file"],
                fused_score=final_score,
                retrieval_paths=data["paths"],
                path_scores=dict(chunk_scores[chunk_id]),
                path_ranks=dict(chunk_ranks[chunk_id]),
                metadata=data["metadata"],
            ))
        
        # Sort by fused score (or by time if temporal)
        if temporal_sort:
            fused_results.sort(
                key=lambda x: x.metadata.get("created_at", ""),
                reverse=True
            )
        else:
            fused_results.sort(key=lambda x: x.fused_score, reverse=True)
        
        # Return top-k
        final = fused_results[:top_k]
        
        logger.info(
            "rrf_fusion_complete",
            input_count=len(chunk_data),
            output_count=len(final),
            multi_path_count=sum(1 for r in final if r.found_by_multiple),
        )
        
        return final
    
    def _calculate_recency(self, metadata: dict) -> float:
        """
        Calculate recency factor (0-1, 1 = very recent).
        
        Uses exponential decay based on halflife.
        """
        created_at = metadata.get("created_at")
        if not created_at:
            return 0.5  # Default for unknown dates
        
        try:
            if isinstance(created_at, str):
                # Parse ISO format
                created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                created_dt = created_at
            
            now = datetime.now(created_dt.tzinfo) if created_dt.tzinfo else datetime.now()
            age_days = (now - created_dt).days
            
            # Exponential decay: 0.5^(age/halflife)
            decay = 0.5 ** (age_days / self.recency_halflife_days)
            return decay
            
        except Exception:
            return 0.5
    
    def fuse_with_weights(
        self,
        bundle: RetrievalBundle,
        weights: dict[str, float],
        top_k: int = 10,
    ) -> list[FusedResult]:
        """
        Fuse with custom weights for each path.
        
        Args:
            bundle: RetrievalBundle
            weights: {"dense": 0.5, "sparse": 0.3, "graph": 0.2}
            top_k: Number of results
            
        Returns:
            Weighted fused results
        """
        # Normalize weights
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        chunk_data: dict[str, dict] = {}
        chunk_scores: dict[str, float] = defaultdict(float)
        
        for path_name, results in [
            ("dense", bundle.dense_results),
            ("sparse", bundle.sparse_results),
            ("graph", bundle.graph_results),
        ]:
            path_weight = weights.get(path_name, 0.33)
            
            for result in results:
                cid = result.chunk_id
                
                if cid not in chunk_data:
                    chunk_data[cid] = {
                        "content": result.content,
                        "source_file": result.source_file,
                        "metadata": result.metadata,
                        "paths": [],
                        "path_scores": {},
                    }
                
                chunk_data[cid]["paths"].append(path_name)
                chunk_data[cid]["path_scores"][path_name] = result.score
                chunk_scores[cid] += path_weight * result.score
        
        fused_results = []
        for chunk_id, data in chunk_data.items():
            fused_results.append(FusedResult(
                chunk_id=chunk_id,
                content=data["content"],
                source_file=data["source_file"],
                fused_score=chunk_scores[chunk_id],
                retrieval_paths=data["paths"],
                path_scores=data["path_scores"],
                path_ranks={},  # Not calculated in weighted mode
                metadata=data["metadata"],
            ))
        
        fused_results.sort(key=lambda x: x.fused_score, reverse=True)
        return fused_results[:top_k]


def build_context_string(results: list[FusedResult], max_chars: int = 8000) -> str:
    """
    Build context string for LLM from fused results.
    
    Formats results as numbered sources that can be cited.
    """
    context_parts = []
    char_count = 0
    
    for i, result in enumerate(results, start=1):
        source_label = result.citation_label
        
        source_block = f"[Source {i}: {source_label}]\n{result.content}\n"
        
        if char_count + len(source_block) > max_chars:
            break
        
        context_parts.append(source_block)
        char_count += len(source_block)
    
    return "\n".join(context_parts)
