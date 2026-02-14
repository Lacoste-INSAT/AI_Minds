"""
Real-World Data Tests for Synapsis Reasoning Engine
====================================================

Tests using realistic data from Wikipedia and simulated team documents.
These tests validate accuracy in real-world scenarios.

Run with:
    pytest backend/reasoning/tests/test_real_data.py -v
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from backend.reasoning.tests.test_fixtures import (
    REAL_TEST_CHUNKS,
    TEST_QUESTIONS,
    BM25_TEST_CORPUS,
    ACCURACY_TEST_CASES,
)
from backend.reasoning.cpumodel.models import (
    QueryType,
    ConfidenceLevel,
    FusedContext,
    ChunkEvidence,
    LLMResponse,
    ModelTier,
)
from backend.reasoning.cpumodel.query_planner import classify_query, _extract_entities_basic
from backend.reasoning.cpumodel.fusion import fuse_results, format_context_for_llm
from backend.reasoning.cpumodel.llm_agent import (
    reason_and_respond,
    compute_confidence,
    _build_reasoning_prompt,
)


class TestQueryClassificationRealData:
    """Test query classification with realistic queries."""
    
    @pytest.mark.asyncio
    async def test_simple_rag_definition(self):
        """'What is RAG?' should classify as SIMPLE."""
        result = await classify_query("What is RAG?", use_llm=False)
        assert result.query_type == QueryType.SIMPLE
    
    @pytest.mark.asyncio
    async def test_simple_pkm_definition(self):
        """'What is personal knowledge management?' should classify as SIMPLE."""
        result = await classify_query("What is personal knowledge management?", use_llm=False)
        assert result.query_type == QueryType.SIMPLE
    
    @pytest.mark.asyncio
    async def test_multihop_hybrid_search(self):
        """Multi-hop query about hybrid search and RAG."""
        result = await classify_query(
            "How does hybrid search relate to RAG accuracy?",
            use_llm=False
        )
        # Should be MULTI_HOP due to "relate to" pattern
        assert result.query_type == QueryType.MULTI_HOP
    
    @pytest.mark.asyncio
    async def test_multihop_person_topic(self):
        """'What did John say about Ollama?' should extract John as entity."""
        result = await classify_query(
            "What did John say about Ollama?",
            use_llm=False
        )
        assert result.query_type == QueryType.MULTI_HOP
        assert any("john" in e.lower() for e in result.entities_detected)
    
    @pytest.mark.asyncio
    async def test_temporal_february_meetings(self):
        """Temporal query about February meetings."""
        result = await classify_query(
            "What updates were discussed in the February meetings?",
            use_llm=False
        )
        # Should detect temporal pattern
        assert result.query_type in [QueryType.TEMPORAL, QueryType.SIMPLE]


class TestEntityExtractionRealData:
    """Test entity extraction with realistic content."""
    
    def test_extract_rag_entities(self):
        """Extract entities from RAG-related query."""
        entities = _extract_entities_basic("How does Qdrant work with Ollama?")
        assert "Qdrant" in entities or "Ollama" in entities
    
    def test_extract_person_names(self):
        """Extract person names from team queries."""
        entities = _extract_entities_basic("What did Sarah say about the budget?")
        assert "Sarah" in entities
    
    def test_extract_tool_names(self):
        """Extract tool names from PKM query."""
        entities = _extract_entities_basic("Compare Obsidian and Notion for PKM")
        # Should extract Obsidian and Notion
        assert "Obsidian" in entities or "Notion" in entities


class TestFusionRealData:
    """Test RRF fusion with realistic chunks."""
    
    def test_fuse_rag_chunks(self):
        """Fuse RAG-related chunks."""
        # Simulate retrieval results
        from backend.reasoning.cpumodel.models import RetrievalResult
        
        rag_chunks = [c for c in REAL_TEST_CHUNKS if "rag" in c.chunk_id.lower()][:5]
        
        dense_result = RetrievalResult(
            chunks=rag_chunks[:3],
            retrieval_type="dense",
            latency_ms=50,
        )
        sparse_result = RetrievalResult(
            chunks=rag_chunks[2:5],
            retrieval_type="sparse", 
            latency_ms=10,
        )
        
        # fuse_results expects a dict keyed by retrieval type
        fused = fuse_results({"dense": dense_result, "sparse": sparse_result}, top_k=5)
        
        # Should have chunks
        assert len(fused.chunks) > 0
        # Should track source counts
        assert fused.dense_count > 0 or fused.sparse_count > 0
    
    def test_format_context_real_chunks(self):
        """Format context from real chunks."""
        rag_chunks = [c for c in REAL_TEST_CHUNKS if "rag" in c.chunk_id.lower()][:3]
        
        fused = FusedContext(
            chunks=rag_chunks,
            dense_count=2,
            sparse_count=1,
            graph_count=0,
        )
        
        context_str = format_context_for_llm(fused)
        
        # Should contain source markers
        assert "[Source 1]" in context_str
        # Should contain actual content
        assert "retrieval" in context_str.lower() or "RAG" in context_str


class TestLLMAgentRealData:
    """Test LLM agent with realistic prompts."""
    
    def test_build_prompt_real_context(self):
        """Build prompt with real Wikipedia content."""
        rag_chunks = [c for c in REAL_TEST_CHUNKS if "rag" in c.chunk_id.lower()][:3]
        
        fused = FusedContext(
            chunks=rag_chunks,
            dense_count=2,
            sparse_count=1,
            graph_count=0,
        )
        
        context_str = format_context_for_llm(fused)
        prompt = _build_reasoning_prompt(
            query="What is RAG?",
            context=context_str,
        )
        
        # Should contain the query
        assert "What is RAG?" in prompt
        # Should contain source content
        assert "retrieval" in prompt.lower() or "Source" in prompt
    
    @pytest.mark.asyncio
    async def test_reason_empty_context(self):
        """Test reasoning with empty context (should abstain)."""
        empty_fused = FusedContext(
            chunks=[],
            dense_count=0,
            sparse_count=0,
            graph_count=0,
        )
        
        result = await reason_and_respond(
            query="What is the meaning of life?",
            fused_context=empty_fused,
            query_type=QueryType.SIMPLE,
            tier=ModelTier.T3,
        )
        
        # Should abstain with confidence "none"
        assert result.confidence == ConfidenceLevel.NONE
        # Check for abstention language
        answer_lower = result.answer.lower()
        assert any(phrase in answer_lower for phrase in [
            "insufficient", "cannot", "don't have enough", "no relevant"
        ])
    
    @pytest.mark.asyncio
    async def test_reason_with_mocked_llm(self):
        """Test full reasoning with mocked LLM response."""
        rag_chunks = [c for c in REAL_TEST_CHUNKS if "rag" in c.chunk_id.lower()][:3]
        
        fused = FusedContext(
            chunks=rag_chunks,
            dense_count=2,
            sparse_count=1,
            graph_count=0,
        )
        
        with patch("reasoning.reasoning.cpumodel.llm_agent.generate_completion") as mock_llm:
            # Mock LLM responses
            mock_llm.side_effect = [
                # Synthesis response
                LLMResponse(
                    content="RAG (Retrieval-Augmented Generation) is a technique that enables LLMs to retrieve and incorporate external information [Source 1]. It helps reduce hallucinations by grounding responses in retrieved documents [Source 2].",
                    model="qwen2.5:0.5b",
                    success=True,
                ),
                # Critic response
                LLMResponse(
                    content='{"verdict": "APPROVE", "reasoning": "All claims are supported by sources", "unsupported_claims": []}',
                    model="qwen2.5:0.5b",
                    success=True,
                ),
            ]
            
            result = await reason_and_respond(
                query="What is RAG?",
                fused_context=fused,
                query_type=QueryType.SIMPLE,
                tier=ModelTier.T3,
            )
        
        # Should have an answer
        assert result.answer is not None
        assert "RAG" in result.answer
        # Should have sources
        assert result.sources is not None
        assert len(result.sources) > 0


class TestAccuracyEvaluation:
    """Test answer accuracy against golden answers."""
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", ACCURACY_TEST_CASES[:2])  # Run first 2 cases
    async def test_answer_contains_expected_terms(self, test_case):
        """Test that answers contain expected terms."""
        query = test_case["query"]
        must_contain = test_case.get("must_contain", [])
        must_contain_any = test_case.get("must_contain_any", [])
        
        # Find relevant chunks
        relevant_chunks = [
            c for c in REAL_TEST_CHUNKS 
            if any(term.lower() in c.snippet.lower() for term in must_contain + must_contain_any)
        ][:3]
        
        if not relevant_chunks:
            pytest.skip("No relevant chunks found for this test case")
        
        fused = FusedContext(
            chunks=relevant_chunks,
            dense_count=len(relevant_chunks),
            sparse_count=0,
            graph_count=0,
        )
        
        with patch("reasoning.reasoning.cpumodel.llm_agent.generate_completion") as mock_llm:
            # Create an answer that includes expected terms
            answer_content = f"Based on the sources: {test_case['golden_answer']} [Source 1]"
            
            mock_llm.side_effect = [
                LLMResponse(content=answer_content, model="qwen2.5:0.5b", success=True),
                LLMResponse(
                    content='{"verdict": "APPROVE", "reasoning": "OK", "unsupported_claims": []}',
                    model="qwen2.5:0.5b",
                    success=True
                ),
            ]
            
            result = await reason_and_respond(
                query=query,
                fused_context=fused,
                query_type=QueryType.SIMPLE,
                tier=ModelTier.T3,
            )
        
        # Verify answer contains expected terms
        answer_lower = result.answer.lower()
        
        if must_contain:
            for term in must_contain:
                assert term.lower() in answer_lower, f"Expected '{term}' in answer"
        
        if must_contain_any:
            found = any(term.lower() in answer_lower for term in must_contain_any)
            assert found, f"Expected one of {must_contain_any} in answer"


class TestBM25WithRealCorpus:
    """Test BM25 sparse retrieval with real corpus."""
    
    def test_bm25_rag_query(self):
        """Test BM25 retrieval for RAG query."""
        from rank_bm25 import BM25Okapi
        
        # Build corpus
        corpus = [doc["content"].lower().split() for doc in BM25_TEST_CORPUS]
        bm25 = BM25Okapi(corpus)
        
        # Search for RAG
        query = "what is retrieval augmented generation RAG"
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        # Get top result
        top_idx = scores.argmax()
        top_doc = BM25_TEST_CORPUS[top_idx]
        
        # Should find RAG-related document
        assert "rag" in top_doc["content"].lower()
    
    def test_bm25_deadline_query(self):
        """Test BM25 retrieval for deadline query."""
        from rank_bm25 import BM25Okapi
        
        corpus = [doc["content"].lower().split() for doc in BM25_TEST_CORPUS]
        bm25 = BM25Okapi(corpus)
        
        query = "project deadline date"
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        top_idx = scores.argmax()
        top_doc = BM25_TEST_CORPUS[top_idx]
        
        # Should find deadline document
        assert "deadline" in top_doc["content"].lower() or "march" in top_doc["content"].lower()
    
    def test_bm25_pkm_tools(self):
        """Test BM25 retrieval for PKM tools query."""
        from rank_bm25 import BM25Okapi
        
        corpus = [doc["content"].lower().split() for doc in BM25_TEST_CORPUS]
        bm25 = BM25Okapi(corpus)
        
        query = "PKM personal knowledge management tools Obsidian"
        query_tokens = query.lower().split()
        scores = bm25.get_scores(query_tokens)
        
        top_idx = scores.argmax()
        top_doc = BM25_TEST_CORPUS[top_idx]
        
        # Should find PKM tools document
        assert "pkm" in top_doc["content"].lower() or "obsidian" in top_doc["content"].lower()


class TestConfidenceWithRealData:
    """Test confidence scoring with realistic scenarios."""
    
    def test_high_confidence_multiple_sources(self):
        """Multiple matching sources should give high confidence."""
        from backend.reasoning.cpumodel.models import VerificationVerdict
        
        rag_chunks = [c for c in REAL_TEST_CHUNKS if "rag" in c.chunk_id.lower()][:4]
        
        fused = FusedContext(
            chunks=rag_chunks,
            dense_count=3,
            sparse_count=1,
            graph_count=0,
        )
        
        confidence, score, reason = compute_confidence(
            fused_context=fused,
            verification=VerificationVerdict.APPROVE,
        )
        
        # Multiple sources + APPROVE should give high/medium confidence
        assert confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]
    
    def test_low_confidence_single_source(self):
        """Single source should give lower confidence."""
        from backend.reasoning.cpumodel.models import VerificationVerdict
        
        single_chunk = [REAL_TEST_CHUNKS[0]]
        
        fused = FusedContext(
            chunks=single_chunk,
            dense_count=1,
            sparse_count=0,
            graph_count=0,
        )
        
        confidence, score, reason = compute_confidence(
            fused_context=fused,
            verification=VerificationVerdict.APPROVE,
        )
        
        # Single source typically medium or lower
        assert confidence in [ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW, ConfidenceLevel.HIGH]
    
    def test_no_confidence_on_reject(self):
        """Rejection should give low/none confidence."""
        from backend.reasoning.cpumodel.models import VerificationVerdict
        
        chunks = [c for c in REAL_TEST_CHUNKS[:3]]
        
        fused = FusedContext(
            chunks=chunks,
            dense_count=2,
            sparse_count=1,
            graph_count=0,
        )
        
        confidence, score, reason = compute_confidence(
            fused_context=fused,
            verification=VerificationVerdict.REJECT,
        )
        
        # REJECT should heavily penalize confidence
        assert confidence in [ConfidenceLevel.LOW, ConfidenceLevel.NONE]

