"""
Integration tests for the full reasoning pipeline.
Tests end-to-end flow without external dependencies.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class TestFullPipelineWithMocks:
    """Test complete query -> answer pipeline with mocked dependencies."""
    
    @pytest.mark.asyncio
    async def test_simple_query_pipeline(self):
        """Test SIMPLE query through full pipeline with mocked retrieval."""
        from backend.reasoning.cpumodel.models import (
            QueryType, ConfidenceLevel, VerificationVerdict, ModelTier,
            FusedContext, ChunkEvidence
        )
        from backend.reasoning.cpumodel.llm_agent import reason_and_respond
        
        # Create mock fused context with real chunks
        mock_chunks = [
            ChunkEvidence(
                chunk_id="chunk_001",
                document_id="doc_001",
                file_name="meeting_notes.txt",
                snippet="The project deadline is March 15th as confirmed by John.",
                score_final=0.85,
            ),
        ]
        fused = FusedContext(
            chunks=mock_chunks,
            dense_count=1,
            sparse_count=0,
            graph_count=0,
        )
        
        # Mock the Ollama client to avoid needing actual LLM
        with patch("reasoning.reasoning.cpumodel.llm_agent.generate_completion") as mock_llm:
            # Mock synthesis response
            from backend.reasoning.cpumodel.models import LLMResponse
            mock_llm.side_effect = [
                # First call: synthesis
                LLMResponse(
                    content="The project deadline is March 15th [Source 1].",
                    model="qwen2.5:0.5b",
                    success=True,
                ),
                # Second call: critic
                LLMResponse(
                    content='{"verdict": "APPROVE", "reasoning": "Supported", "unsupported_claims": []}',
                    model="qwen2.5:0.5b",
                    success=True,
                ),
            ]
            
            result = await reason_and_respond(
                query="What is the project deadline?",
                fused_context=fused,
                query_type=QueryType.SIMPLE,
                tier=ModelTier.T3,
            )
        
        # Verify answer structure per Section 9.3
        assert result.answer is not None
        assert len(result.answer) > 0
        assert result.confidence is not None
        assert result.verification is not None
        assert result.sources is not None
        assert result.model_used == ModelTier.T3
        
        # Verify content
        assert "March 15" in result.answer
    
    @pytest.mark.asyncio
    async def test_multi_hop_query_uses_graph(self):
        """Test MULTI_HOP query attempts graph retrieval."""
        from backend.reasoning.cpumodel.query_planner import classify_query
        from backend.reasoning.cpumodel.models import QueryType
        
        # Use classify_query with use_llm=False to test heuristics only
        plan = await classify_query("What did John say about the project?", use_llm=False)
        
        # Should classify as MULTI_HOP based on "did X say about" pattern
        assert plan.query_type == QueryType.MULTI_HOP
        # Should detect "John" as entity
        assert any("john" in e.lower() for e in plan.entities_detected)


class TestPipelineEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.mark.asyncio
    async def test_handles_empty_query(self):
        """Empty query should not crash."""
        from backend.reasoning.cpumodel.query_planner import classify_query
        
        result = await classify_query("", use_llm=False)
        assert result is not None
        assert result.original_query == ""
    
    @pytest.mark.asyncio
    async def test_handles_very_long_query(self):
        """Very long query should be handled."""
        from backend.reasoning.cpumodel.query_planner import classify_query
        
        long_query = "What is the deadline? " * 100
        result = await classify_query(long_query, use_llm=False)
        assert result is not None
    
    def test_fusion_handles_all_empty(self):
        """Fusion with all empty results should not crash."""
        from backend.reasoning.cpumodel.fusion import fuse_results
        from backend.reasoning.cpumodel.models import RetrievalResult
        
        results = {
            "dense": RetrievalResult(chunks=[], retrieval_type="dense"),
            "sparse": RetrievalResult(chunks=[], retrieval_type="sparse"),
            "graph": RetrievalResult(chunks=[], retrieval_type="graph"),
        }
        
        fused = fuse_results(results)
        assert len(fused.chunks) == 0
        assert fused.dense_count == 0


class TestContractCompliance:
    """Verify implementation matches ARCHITECTURE.md contracts."""
    
    def test_answer_packet_has_required_fields(self):
        """AnswerPacket must have all fields per Section 9.1."""
        from backend.reasoning.cpumodel.models import (
            AnswerPacket, ConfidenceLevel, VerificationVerdict,
            QueryType, ModelTier
        )
        
        # Create minimal valid packet
        packet = AnswerPacket(
            answer="Test answer",
            confidence=ConfidenceLevel.MEDIUM,
            confidence_score=0.5,
            sources=[],
            verification=VerificationVerdict.APPROVE,
            query_type=QueryType.SIMPLE,
            model_used=ModelTier.T3,
        )
        
        # All required fields from Section 9.3
        assert hasattr(packet, 'answer')
        assert hasattr(packet, 'confidence')
        assert hasattr(packet, 'confidence_score')
        assert hasattr(packet, 'sources')
        assert hasattr(packet, 'verification')
        assert hasattr(packet, 'reasoning_chain')  # Optional but present
    
    def test_default_model_is_t3(self):
        """Default should be T3 (CPU) per our CPU-only requirement."""
        from backend.reasoning.cpumodel.ollama_client import DEFAULT_TIER
        from backend.reasoning.cpumodel.models import ModelTier
        
        assert DEFAULT_TIER == ModelTier.T3
        assert DEFAULT_TIER.value == "qwen2.5:0.5b"

