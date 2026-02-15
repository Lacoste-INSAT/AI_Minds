"""
Test suite for cpumodel Retrieval & Reasoning Engine
Mirrors the gpumodel test structure for consistency.

Run: python -m pytest backend/reasoning/cpumodel/test_cpumodel.py -v
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


# =============================================================================
# Test Query Planner (Intent Detector)
# =============================================================================

class TestQueryPlanner:
    """Tests for query classification."""
    
    def test_simple_query_detection(self):
        """Simple factual queries should fallback to None (needs LLM)."""
        from backend.reasoning.cpumodel.query_planner import _classify_by_heuristics
        
        result = _classify_by_heuristics("What is the budget?")
        # No temporal/multi-hop keywords = None (needs LLM)
        assert result is None
    
    def test_temporal_query_detection(self):
        """Temporal queries should be detected by keywords."""
        from backend.reasoning.cpumodel.query_planner import _classify_by_heuristics
        from backend.reasoning.cpumodel.models import QueryType
        
        result = _classify_by_heuristics("How has my view on X changed over time?")
        assert result == QueryType.TEMPORAL
        
        result = _classify_by_heuristics("What was the progress last week?")
        assert result == QueryType.TEMPORAL
    
    def test_multi_hop_detection(self):
        """Multi-hop queries need relationship traversal."""
        from backend.reasoning.cpumodel.query_planner import _classify_by_heuristics
        from backend.reasoning.cpumodel.models import QueryType
        
        result = _classify_by_heuristics("What did Sarah say about the budget?")
        assert result == QueryType.MULTI_HOP
        
        result = _classify_by_heuristics("How does project Alpha connect to the marketing?")
        assert result == QueryType.MULTI_HOP
    
    def test_contradiction_detection(self):
        """Contradiction queries should be detected."""
        from backend.reasoning.cpumodel.query_planner import _classify_by_heuristics
        from backend.reasoning.cpumodel.models import QueryType
        
        result = _classify_by_heuristics("Did I say conflicting things about the deadline?")
        assert result == QueryType.CONTRADICTION
    
    def test_entity_extraction(self):
        """Should extract capitalized names as potential entities."""
        from backend.reasoning.cpumodel.query_planner import _extract_entities_basic
        
        entities = _extract_entities_basic("What did Sarah say about Project Alpha?")
        assert "Sarah" in entities
        assert "Project" in entities or "Alpha" in entities


# =============================================================================
# Test RRF Fusion (Context Assembler)
# =============================================================================

class TestRRFFusion:
    """Tests for result fusion."""
    
    def test_rrf_score_calculation(self):
        """RRF should combine results from multiple paths."""
        from backend.reasoning.cpumodel.fusion import fuse_results
        from backend.reasoning.cpumodel.models import ChunkEvidence, RetrievalResult
        
        # Create mock results
        dense_chunk = ChunkEvidence(
            chunk_id="chunk1",
            document_id="doc1",
            file_name="doc1.md",
            snippet="Dense result 1",
            score_dense=0.9,
        )
        
        sparse_chunk = ChunkEvidence(
            chunk_id="chunk1",  # Same chunk
            document_id="doc1",
            file_name="doc1.md",
            snippet="Dense result 1",
            score_sparse=0.8,
        )
        
        sparse_only = ChunkEvidence(
            chunk_id="chunk2",
            document_id="doc2",
            file_name="doc2.md",
            snippet="Sparse only",
            score_sparse=0.6,
        )
        
        retrieval_results = {
            "dense": RetrievalResult(chunks=[dense_chunk], retrieval_type="dense"),
            "sparse": RetrievalResult(chunks=[sparse_chunk, sparse_only], retrieval_type="sparse"),
        }
        
        fused = fuse_results(retrieval_results, top_k=5)
        
        # chunk1 should be top (found by both paths)
        assert fused.chunks[0].chunk_id == "chunk1"
        assert fused.chunks[0].score_final > fused.chunks[1].score_final
    
    def test_deduplication(self):
        """Same chunk from multiple paths should be deduplicated."""
        from backend.reasoning.cpumodel.fusion import fuse_results
        from backend.reasoning.cpumodel.models import ChunkEvidence, RetrievalResult
        
        chunk = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="file.md",
            snippet="content",
            score_dense=0.9,
            score_sparse=0.8,
        )
        
        retrieval_results = {
            "dense": RetrievalResult(chunks=[chunk], retrieval_type="dense"),
            "sparse": RetrievalResult(chunks=[chunk], retrieval_type="sparse"),
        }
        
        fused = fuse_results(retrieval_results, top_k=10)
        
        # Should only have one result (deduplicated)
        assert len(fused.chunks) == 1


# =============================================================================
# Test Confidence Scorer
# =============================================================================

class TestConfidenceScorer:
    """Tests for confidence calculation."""
    
    def test_high_confidence(self):
        """Strong signals should produce higher confidence."""
        from backend.reasoning.cpumodel.llm_agent import compute_confidence
        from backend.reasoning.cpumodel.models import (
            ConfidenceLevel, FusedContext, ChunkEvidence, VerificationVerdict
        )
        
        # Good context with multiple chunks
        chunks = [
            ChunkEvidence(
                chunk_id=f"c{i}",
                document_id=f"d{i}",
                file_name=f"file{i}.md",
                snippet=f"content {i}",
                score_final=0.1,  # RRF scores
            )
            for i in range(4)
        ]
        
        context = FusedContext(chunks=chunks, dense_count=2, sparse_count=2)
        
        # Approved by critic
        level, score, reason = compute_confidence(context, VerificationVerdict.APPROVE)
        
        # Should be at least MEDIUM with good sources
        assert level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        assert score >= 0.4
    
    def test_low_confidence_on_rejection(self):
        """Critic rejection should lower confidence."""
        from backend.reasoning.cpumodel.llm_agent import compute_confidence
        from backend.reasoning.cpumodel.models import (
            ConfidenceLevel, FusedContext, ChunkEvidence, VerificationVerdict
        )
        
        chunks = [
            ChunkEvidence(
                chunk_id="c1",
                document_id="d1",
                file_name="file.md",
                snippet="content",
                score_final=0.1,
            )
        ]
        
        context = FusedContext(chunks=chunks, dense_count=1)
        
        # Rejected by critic
        level, score, reason = compute_confidence(context, VerificationVerdict.REJECT)
        
        # Should be LOW or NONE
        assert level in [ConfidenceLevel.LOW, ConfidenceLevel.NONE]
        assert score < 0.4


# =============================================================================
# Test Hybrid Retriever
# =============================================================================

class TestHybridRetriever:
    """Tests for hybrid retrieval."""
    
    @pytest.mark.asyncio
    async def test_retriever_instantiation(self):
        """HybridRetriever should instantiate correctly."""
        from backend.reasoning.cpumodel.retrieval import HybridRetriever
        
        retriever = HybridRetriever()
        
        assert retriever.dense is not None
        assert retriever.sparse is not None
        assert retriever.graph is not None
    
    @pytest.mark.asyncio
    async def test_retrieve_method_exists(self):
        """retrieve() method should exist and be async."""
        from backend.reasoning.cpumodel.retrieval import HybridRetriever
        from backend.reasoning.cpumodel.models import QueryType
        
        retriever = HybridRetriever()
        
        # Method should exist
        assert hasattr(retriever, 'retrieve')
        
        # Method should be async
        import inspect
        assert inspect.iscoroutinefunction(retriever.retrieve)


# =============================================================================
# Test Engine
# =============================================================================

class TestReasoningEngine:
    """Tests for the ReasoningEngine class."""
    
    def test_engine_instantiation(self):
        """ReasoningEngine should instantiate correctly."""
        from backend.reasoning.cpumodel.engine import ReasoningEngine
        from backend.reasoning.cpumodel.models import ModelTier
        
        engine = ReasoningEngine()
        
        assert engine.default_tier == ModelTier.T3
    
    def test_get_engine(self):
        """get_engine should return singleton."""
        from backend.reasoning.cpumodel.engine import get_engine, ReasoningEngine
        
        engine1 = get_engine()
        engine2 = get_engine()
        
        assert engine1 is engine2
        assert isinstance(engine1, ReasoningEngine)
    
    def test_get_engine_force_new(self):
        """get_engine(force_new=True) should create new instance."""
        from backend.reasoning.cpumodel.engine import get_engine
        
        engine1 = get_engine()
        engine2 = get_engine(force_new=True)
        
        assert engine1 is not engine2


# =============================================================================
# Test Imports
# =============================================================================

class TestImports:
    """Tests that all exports work correctly."""
    
    def test_all_exports(self):
        """All __all__ exports should be importable."""
        from backend.reasoning.cpumodel import (
            # Main Entry Points
            ask, process_query, get_engine, init_engine, ReasoningEngine,
            # Query Planning
            plan_query, classify_query,
            # Retrieval
            hybrid_retrieve, get_retriever, HybridRetriever,
            # Fusion
            fuse_results, format_context_for_llm,
            # LLM Agent
            reason_and_respond, synthesize_answer, verify_answer, compute_confidence,
            # Data Models
            AnswerPacket, ChunkEvidence, ConfidenceLevel, FusedContext,
            LLMResponse, ModelTier, QueryPlan, QueryType, RetrievalResult,
            VerificationVerdict,
            # Client Classes
            get_ollama_client, OllamaClient,
        )
        
        # Just checking imports work
        assert ask is not None
        assert ReasoningEngine is not None
        assert HybridRetriever is not None


# =============================================================================
# Run tests directly
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
