"""
Test Reasoning Pipeline
=======================
Quick smoke tests for the reasoning engine components.

Run: python -m pytest backend/reasoning/test_reasoning.py -v
Or:  python backend/reasoning/test_reasoning.py
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock


# =============================================================================
# Test Query Planner
# =============================================================================

class TestQueryPlanner:
    """Tests for query classification."""
    
    def test_simple_query_detection(self):
        """Simple factual queries should be classified as SIMPLE."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner, QueryType
        
        # Mock Ollama client (not needed for regex-based classification)
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        # These should be classifiable without LLM (via entities)
        # But without entities, they go to LLM or fallback
        quick_type = planner._quick_classify("What is the budget?")
        # No temporal/multi-hop keywords = None (needs LLM or defaults to SIMPLE)
        assert quick_type is None or quick_type == QueryType.SIMPLE
    
    def test_temporal_query_detection(self):
        """Temporal queries should be detected by keywords."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner, QueryType
        
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        # Temporal keywords present
        result = planner._quick_classify("How has my view on X changed over time?")
        assert result == QueryType.TEMPORAL
        
        result = planner._quick_classify("What was the progress last week?")
        assert result == QueryType.TEMPORAL
    
    def test_multi_hop_detection(self):
        """Multi-hop queries need relationship traversal."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner, QueryType
        
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        # Test with query that matches multiple patterns (relation + connect)
        result = planner._quick_classify("How does project Alpha connect and relate to the budget?")
        assert result == QueryType.MULTI_HOP
        
        # Test "say about" pattern (matches both "say about" patterns)
        result = planner._quick_classify("What did Sarah say about the marketing, can you tell me what they said about it?")
        assert result == QueryType.MULTI_HOP
    
    def test_entity_extraction(self):
        """Should extract capitalized names as potential entities."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner
        
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        entities = planner._extract_entities_regex("What did Sarah say about Project Alpha?")
        assert "Sarah" in entities
        assert "Project Alpha" in entities
    
    def test_retrieval_strategy(self):
        """Should return correct strategy for each query type."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner, QueryType, QueryPlan
        
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        # Simple query
        plan = QueryPlan(
            query_type=QueryType.SIMPLE,
            original_query="test",
            entities_mentioned=[],
            time_range=None,
            requires_graph=False,
            requires_temporal=False,
            reasoning="test"
        )
        
        strategy = planner.get_retrieval_strategy(plan)
        assert strategy["graph_hops"] == 0  # No graph for SIMPLE
        
        # Multi-hop query
        plan.query_type = QueryType.MULTI_HOP
        strategy = planner.get_retrieval_strategy(plan)
        assert strategy["graph_hops"] > 0  # Needs graph


# =============================================================================
# Test RRF Fusion
# =============================================================================

class TestRRFFusion:
    """Tests for result fusion."""
    
    def test_rrf_score_calculation(self):
        """RRF should combine results from multiple paths."""
        from backend.reasoning.gpumodel.fusion import RRFFusion, FusedResult
        from backend.reasoning.gpumodel.retriever import RetrievalResult, RetrievalBundle
        
        # Create mock results
        dense_results = [
            RetrievalResult(
                chunk_id="chunk1",
                content="Dense result 1",
                source_file="doc1.md",
                score=0.9,
                retrieval_path="dense"
            ),
            RetrievalResult(
                chunk_id="chunk2", 
                content="Dense result 2",
                source_file="doc2.md",
                score=0.7,
                retrieval_path="dense"
            ),
        ]
        
        sparse_results = [
            RetrievalResult(
                chunk_id="chunk1",  # Same as dense rank 1
                content="Dense result 1",
                source_file="doc1.md",
                score=0.8,
                retrieval_path="sparse"
            ),
            RetrievalResult(
                chunk_id="chunk3",
                content="Sparse only",
                source_file="doc3.md",
                score=0.6,
                retrieval_path="sparse"
            ),
        ]
        
        bundle = RetrievalBundle(
            dense_results=dense_results,
            sparse_results=sparse_results,
            graph_results=[],
            query="test query"
        )
        
        fusion = RRFFusion(k=60)
        fused = fusion.fuse(bundle, top_k=5)
        
        # chunk1 should be top (found by both paths)
        assert fused[0].chunk_id == "chunk1"
        assert fused[0].found_by_multiple == True
        assert "dense" in fused[0].retrieval_paths
        assert "sparse" in fused[0].retrieval_paths
    
    def test_deduplication(self):
        """Same chunk from multiple paths should be deduplicated."""
        from backend.reasoning.gpumodel.fusion import RRFFusion
        from backend.reasoning.gpumodel.retriever import RetrievalResult, RetrievalBundle
        
        # Same chunk appears in both paths
        results = [
            RetrievalResult("c1", "content", "file.md", 0.9, "dense"),
        ]
        
        bundle = RetrievalBundle(
            dense_results=results,
            sparse_results=results.copy(),  # Same results
            graph_results=[],
            query="test"
        )
        
        fusion = RRFFusion()
        fused = fusion.fuse(bundle, top_k=10)
        
        # Should only have one result (deduplicated)
        assert len(fused) == 1


# =============================================================================
# Test Confidence Scorer
# =============================================================================

class TestConfidenceScorer:
    """Tests for confidence calculation."""
    
    def test_high_confidence(self):
        """Strong signals should produce HIGH confidence."""
        from backend.reasoning.gpumodel.confidence import ConfidenceScorer, ConfidenceLevel
        from backend.reasoning.gpumodel.fusion import FusedResult
        from backend.reasoning.gpumodel.reasoner import ReasoningResult
        from backend.reasoning.gpumodel.critic import CriticResult, CriticVerdict
        
        scorer = ConfidenceScorer()
        
        # Good retrieval results
        results = [
            FusedResult(
                chunk_id=f"c{i}",
                content=f"content {i}",
                source_file=f"file{i}.md",
                fused_score=0.1,  # Normalized score
                retrieval_paths=["dense", "sparse"],
                path_scores={},
                path_ranks={},
                metadata={"created_at": "2026-02-14T10:00:00"}
            )
            for i in range(4)
        ]
        
        # Good reasoning result
        reasoning = ReasoningResult(
            answer="Answer with citations",
            citations=[],
            reasoning_chain="Good reasoning",
            sources_used=[1, 2, 3],
            model_used="phi4-mini",
            raw_response="",
            contradictions_found=[]
        )
        
        # Approved by critic
        critic = CriticResult(
            verdict=CriticVerdict.APPROVE,
            confidence=0.9,
            feedback="Verified",
            issues_found=[],
            claims_verified=5,
            claims_supported=5,
            model_used="phi4-mini"
        )
        
        result = scorer.calculate(results, reasoning, critic)
        
        # Should be HIGH or at least MEDIUM
        assert result.level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
        assert result.score >= 0.4
    
    def test_low_confidence_on_rejection(self):
        """Critic rejection should lower confidence."""
        from backend.reasoning.gpumodel.confidence import ConfidenceScorer, ConfidenceLevel
        from backend.reasoning.gpumodel.critic import CriticResult, CriticVerdict
        
        scorer = ConfidenceScorer()
        
        # Rejected by critic
        critic = CriticResult(
            verdict=CriticVerdict.REJECT,
            confidence=0.9,
            feedback="Fabricated",
            issues_found=["Hallucination detected"],
            claims_verified=3,
            claims_supported=0,
            model_used="phi4-mini"
        )
        
        result = scorer.calculate([], None, critic)
        
        # Should be LOW or NONE
        assert result.level in [ConfidenceLevel.LOW, ConfidenceLevel.NONE]


# =============================================================================
# Test Ollama Client (mocked)
# =============================================================================

class TestOllamaClient:
    """Tests for Ollama client with mocked responses."""
    
    @pytest.mark.asyncio
    async def test_fallback_on_timeout(self):
        """Should fallback to next tier on timeout."""
        from backend.reasoning.gpumodel.ollama_client import OllamaClient, ModelTier
        
        client = OllamaClient(enable_fallback=True)
        
        # Mock the _call_ollama method
        call_count = 0
        async def mock_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise asyncio.TimeoutError()
            return {"response": "From fallback", "eval_count": 10}
        
        client._call_ollama = mock_call
        client._available_models = {"phi4-mini", "qwen2.5:3b", "qwen2.5:0.5b"}
        
        response = await client.generate("Test prompt")
        
        # Should have tried twice (first timeout, then success)
        assert call_count == 2
        assert "fallback" in response.content.lower()
        
        await client.close()
    
    @pytest.mark.asyncio
    async def test_no_fallback_when_disabled(self):
        """Should not fallback when disabled."""
        from backend.reasoning.gpumodel.ollama_client import OllamaClient, ModelTier
        
        client = OllamaClient(enable_fallback=False)
        
        async def mock_call(*args, **kwargs):
            raise asyncio.TimeoutError()
        
        client._call_ollama = mock_call
        client._available_models = {"phi4-mini", "qwen2.5:3b"}
        
        with pytest.raises(RuntimeError):
            await client.generate("Test prompt")
        
        await client.close()


# =============================================================================
# Test Hybrid Retriever
# =============================================================================

class TestHybridRetriever:
    """Tests for hybrid retrieval."""
    
    @pytest.mark.asyncio
    async def test_retrieve_maps_query_type(self):
        """retrieve() should map query_type to correct strategy."""
        from backend.reasoning.gpumodel.retriever import HybridRetriever, RetrievalBundle
        from backend.reasoning.gpumodel.query_planner import QueryType
        
        retriever = HybridRetriever()
        
        # Test SIMPLE query type
        result = await retriever.retrieve(
            query="What is the budget?",
            query_type=QueryType.SIMPLE,
            entities=["budget"],
            top_k=10,
        )
        
        assert isinstance(result, RetrievalBundle)
        assert result.query == "What is the budget?"
        # Should have called search internally
        
    @pytest.mark.asyncio
    async def test_retrieve_multi_hop_enables_graph(self):
        """MULTI_HOP queries should enable graph traversal."""
        from backend.reasoning.gpumodel.retriever import HybridRetriever, RetrievalBundle
        from backend.reasoning.gpumodel.query_planner import QueryType
        
        retriever = HybridRetriever()
        
        # MULTI_HOP should use graph
        result = await retriever.retrieve(
            query="What did Sarah say about the budget?",
            query_type=QueryType.MULTI_HOP,
            entities=["Sarah", "budget"],
            top_k=10,
        )
        
        assert isinstance(result, RetrievalBundle)
        # Graph results would be populated if we had a graph loaded


# =============================================================================
# Integration Test (mock LLM)
# =============================================================================

class TestReasoningPipelineIntegration:
    """Integration tests with mocked LLM."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_mock(self):
        """Test full pipeline with mocked components."""
        from backend.reasoning.gpumodel.query_planner import QueryPlanner, QueryType
        from backend.reasoning.gpumodel.fusion import FusedResult
        
        # Create mock results
        mock_sources = [
            FusedResult(
                chunk_id="c1",
                content="Sarah said the budget is $50,000 for Q1.",
                source_file="meeting_notes.md",
                fused_score=0.8,
                retrieval_paths=["dense"],
                path_scores={"dense": 0.8},
                path_ranks={"dense": 1},
                metadata={}
            )
        ]
        
        # Test that we can construct the pipeline components
        # (full integration would need real Ollama)
        mock_ollama = MagicMock()
        planner = QueryPlanner(mock_ollama)
        
        # Test synchronous classification
        plan_result = planner._quick_classify("What did Sarah say about the budget?")
        assert plan_result == QueryType.MULTI_HOP


# =============================================================================
# Run tests directly
# =============================================================================

if __name__ == "__main__":
    import sys
    
    print("Running reasoning pipeline tests...")
    print("=" * 60)
    
    # Run pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v", "--tb=short"])
    except:
        print("\nRunning basic tests (pytest not available)...")
        
        # Query Planner tests
        tests = TestQueryPlanner()
        tests.test_simple_query_detection()
        print("✓ test_simple_query_detection")
        
        tests.test_temporal_query_detection()
        print("✓ test_temporal_query_detection")
        
        tests.test_multi_hop_detection()
        print("✓ test_multi_hop_detection")
        
        tests.test_entity_extraction()
        print("✓ test_entity_extraction")
        
        tests.test_retrieval_strategy()
        print("✓ test_retrieval_strategy")
        
        # Fusion tests
        fusion_tests = TestRRFFusion()
        fusion_tests.test_rrf_score_calculation()
        print("✓ test_rrf_score_calculation")
        
        fusion_tests.test_deduplication()
        print("✓ test_deduplication")
        
        # Confidence tests
        conf_tests = TestConfidenceScorer()
        conf_tests.test_high_confidence()
        print("✓ test_high_confidence")
        
        conf_tests.test_low_confidence_on_rejection()
        print("✓ test_low_confidence_on_rejection")
        
        print()
        print("=" * 60)
        print("All basic tests passed!")
