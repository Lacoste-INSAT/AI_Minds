"""
Tests for RRF Fusion.
Critical: This merges results from dense/sparse/graph retrieval.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from reasoning.reasoning.cpumodel.fusion import (
    fuse_results,
    format_context_for_llm,
    _compute_rrf_score,
    _compute_recency_factor,
)
from reasoning.reasoning.cpumodel.models import ChunkEvidence, RetrievalResult


class TestRRFScoreComputation:
    """Test the RRF formula implementation."""
    
    def test_single_rank(self):
        """Single rank should give 1/(k+rank)."""
        score = _compute_rrf_score([1], k=60)
        assert score == pytest.approx(1 / 61, rel=1e-6)
    
    def test_multiple_ranks(self):
        """Multiple ranks should sum RRF scores."""
        # Rank 1 in list A, rank 2 in list B
        score = _compute_rrf_score([1, 2], k=60)
        expected = 1/61 + 1/62
        assert score == pytest.approx(expected, rel=1e-6)
    
    def test_empty_ranks(self):
        """Empty ranks should return 0."""
        score = _compute_rrf_score([])
        assert score == 0.0
    
    def test_higher_k_reduces_score(self):
        """Higher k should reduce score."""
        score_low_k = _compute_rrf_score([1], k=10)
        score_high_k = _compute_rrf_score([1], k=100)
        assert score_low_k > score_high_k
    
    def test_lower_rank_higher_score(self):
        """Rank 1 should score higher than rank 10."""
        score_rank_1 = _compute_rrf_score([1], k=60)
        score_rank_10 = _compute_rrf_score([10], k=60)
        assert score_rank_1 > score_rank_10


class TestRecencyFactor:
    """Test recency computation."""
    
    def test_unknown_timestamp_neutral(self):
        """None timestamp should return 0.5 (neutral)."""
        factor = _compute_recency_factor(None)
        assert factor == 0.5
    
    def test_invalid_timestamp_neutral(self):
        """Invalid timestamp should return 0.5."""
        factor = _compute_recency_factor("not-a-date")
        assert factor == 0.5
    
    def test_factor_bounded(self):
        """Factor should always be between 0 and 1."""
        # Test with valid ISO timestamp
        factor = _compute_recency_factor("2026-02-14T10:00:00")
        assert 0.0 <= factor <= 1.0


class TestFuseResults:
    """Test the main fusion function."""
    
    def test_empty_results(self):
        """Empty input should return empty fused context."""
        result = fuse_results({})
        assert len(result.chunks) == 0
    
    def test_single_source_preserved(self):
        """Single retrieval source should pass through."""
        chunk = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="test.txt",
            snippet="Test content",
            score_dense=0.8,
        )
        results = {
            "dense": RetrievalResult(
                chunks=[chunk],
                retrieval_type="dense",
            )
        }
        
        fused = fuse_results(results)
        assert len(fused.chunks) == 1
        assert fused.chunks[0].chunk_id == "c1"
    
    def test_deduplication(self):
        """Same chunk from multiple sources should be deduplicated."""
        chunk_dense = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="test.txt",
            snippet="Test content from dense",
            score_dense=0.8,
        )
        chunk_sparse = ChunkEvidence(
            chunk_id="c1",  # Same ID
            document_id="d1",
            file_name="test.txt",
            snippet="Test content from sparse (longer snippet)",
            score_sparse=0.7,
        )
        
        results = {
            "dense": RetrievalResult(chunks=[chunk_dense], retrieval_type="dense"),
            "sparse": RetrievalResult(chunks=[chunk_sparse], retrieval_type="sparse"),
        }
        
        fused = fuse_results(results)
        # Should have only 1 unique chunk
        assert len(fused.chunks) == 1
        # Should prefer longer snippet
        assert "longer" in fused.chunks[0].snippet
    
    def test_rrf_boosts_multi_source_chunks(self):
        """Chunk in multiple lists should score higher than single-list chunk."""
        # Chunk A: appears in both dense and sparse
        chunk_a_dense = ChunkEvidence(
            chunk_id="a", document_id="d1", file_name="a.txt",
            snippet="A", score_dense=0.5,
        )
        chunk_a_sparse = ChunkEvidence(
            chunk_id="a", document_id="d1", file_name="a.txt",
            snippet="A", score_sparse=0.5,
        )
        
        # Chunk B: only in dense
        chunk_b = ChunkEvidence(
            chunk_id="b", document_id="d1", file_name="b.txt",
            snippet="B", score_dense=0.5,
        )
        
        results = {
            "dense": RetrievalResult(chunks=[chunk_a_dense, chunk_b], retrieval_type="dense"),
            "sparse": RetrievalResult(chunks=[chunk_a_sparse], retrieval_type="sparse"),
        }
        
        fused = fuse_results(results)
        
        # Chunk A should rank higher due to appearing in both lists
        chunk_a_fused = next(c for c in fused.chunks if c.chunk_id == "a")
        chunk_b_fused = next(c for c in fused.chunks if c.chunk_id == "b")
        
        assert chunk_a_fused.score_final > chunk_b_fused.score_final
    
    def test_top_k_limit(self):
        """Should respect top_k limit."""
        chunks = [
            ChunkEvidence(
                chunk_id=f"c{i}",
                document_id="d1",
                file_name="test.txt",
                snippet=f"Content {i}",
                score_dense=0.9 - (i * 0.05),
            )
            for i in range(20)
        ]
        
        results = {
            "dense": RetrievalResult(chunks=chunks, retrieval_type="dense"),
        }
        
        fused = fuse_results(results, top_k=5)
        assert len(fused.chunks) == 5
    
    def test_counts_tracked(self):
        """Should track count from each source."""
        results = {
            "dense": RetrievalResult(
                chunks=[ChunkEvidence(chunk_id="d1", document_id="d", file_name="t", snippet="t", score_dense=0.5)],
                retrieval_type="dense"
            ),
            "sparse": RetrievalResult(
                chunks=[
                    ChunkEvidence(chunk_id="s1", document_id="d", file_name="t", snippet="t", score_sparse=0.5),
                    ChunkEvidence(chunk_id="s2", document_id="d", file_name="t", snippet="t", score_sparse=0.4),
                ],
                retrieval_type="sparse"
            ),
        }
        
        fused = fuse_results(results)
        assert fused.dense_count == 1
        assert fused.sparse_count == 2


class TestFormatContextForLLM:
    """Test context formatting for LLM prompts."""
    
    def test_empty_context(self):
        """Empty chunks should return placeholder."""
        from reasoning.reasoning.cpumodel.models import FusedContext
        fused = FusedContext(chunks=[], dense_count=0, sparse_count=0, graph_count=0)
        formatted = format_context_for_llm(fused)
        assert "No relevant context" in formatted
    
    def test_source_markers(self):
        """Should include [Source N] markers."""
        chunks = [
            ChunkEvidence(
                chunk_id="c1",
                document_id="d1",
                file_name="notes.txt",
                snippet="First chunk content",
                score_final=0.8,
            ),
            ChunkEvidence(
                chunk_id="c2",
                document_id="d2",
                file_name="email.txt",
                snippet="Second chunk content",
                score_final=0.7,
            ),
        ]
        from reasoning.reasoning.cpumodel.models import FusedContext
        fused = FusedContext(chunks=chunks, dense_count=2, sparse_count=0, graph_count=0)
        
        formatted = format_context_for_llm(fused)
        assert "[Source 1]" in formatted
        assert "[Source 2]" in formatted
        assert "notes.txt" in formatted
        assert "email.txt" in formatted
    
    def test_respects_max_chars(self):
        """Should truncate at max_chars."""
        long_snippet = "A" * 5000  # Very long content
        chunks = [
            ChunkEvidence(
                chunk_id="c1",
                document_id="d1",
                file_name="test.txt",
                snippet=long_snippet,
                score_final=0.8,
            )
        ]
        from reasoning.reasoning.cpumodel.models import FusedContext
        fused = FusedContext(chunks=chunks, dense_count=1, sparse_count=0, graph_count=0)
        
        formatted = format_context_for_llm(fused, max_chars=1000)
        assert len(formatted) <= 1500  # Some overhead for markers
