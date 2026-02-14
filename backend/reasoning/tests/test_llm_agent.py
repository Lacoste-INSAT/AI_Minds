"""
Tests for LLM Agent - answer synthesis, verification, and confidence.
"""
import pytest
import sys
import os
from unittest.mock import AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from backend.reasoning.cpumodel.llm_agent import (
    compute_confidence,
    _generate_abstention_response,
    _build_reasoning_prompt,
    _build_critic_prompt,
)
from backend.reasoning.cpumodel.models import (
    ChunkEvidence,
    ConfidenceLevel,
    FusedContext,
    VerificationVerdict,
)


class TestConfidenceScoring:
    """Test confidence computation per ARCHITECTURE.md Section 5.3."""
    
    def test_no_sources_returns_none(self):
        """Empty sources should return NONE confidence."""
        fused = FusedContext(chunks=[], dense_count=0, sparse_count=0, graph_count=0)
        level, score, reason = compute_confidence(fused, VerificationVerdict.APPROVE)
        
        assert level == ConfidenceLevel.NONE
        assert score == 0.0
        assert "No relevant sources" in reason
    
    def test_rejection_penalizes_confidence(self):
        """REJECT verdict should heavily penalize confidence."""
        chunks = [
            ChunkEvidence(
                chunk_id="c1", document_id="d1", file_name="t.txt",
                snippet="Content", score_final=0.5,
            )
        ]
        fused = FusedContext(chunks=chunks, dense_count=1, sparse_count=0, graph_count=0)
        
        level_approve, score_approve, _ = compute_confidence(fused, VerificationVerdict.APPROVE)
        level_reject, score_reject, _ = compute_confidence(fused, VerificationVerdict.REJECT)
        
        assert score_reject < score_approve
        assert score_reject < score_approve * 0.5  # At least 50% penalty
    
    def test_revise_moderately_penalizes(self):
        """REVISE verdict should moderately penalize confidence."""
        chunks = [
            ChunkEvidence(
                chunk_id="c1", document_id="d1", file_name="t.txt",
                snippet="Content", score_final=0.5,
            )
        ]
        fused = FusedContext(chunks=chunks, dense_count=1, sparse_count=0, graph_count=0)
        
        _, score_approve, _ = compute_confidence(fused, VerificationVerdict.APPROVE)
        _, score_revise, _ = compute_confidence(fused, VerificationVerdict.REVISE)
        _, score_reject, _ = compute_confidence(fused, VerificationVerdict.REJECT)
        
        # REVISE should be between APPROVE and REJECT
        assert score_revise < score_approve
        assert score_revise > score_reject
    
    def test_more_sources_increases_confidence(self):
        """More sources should increase confidence."""
        single_chunk = [
            ChunkEvidence(chunk_id="c1", document_id="d1", file_name="t.txt",
                          snippet="Content", score_final=0.5),
        ]
        multiple_chunks = [
            ChunkEvidence(chunk_id=f"c{i}", document_id=f"d{i}", file_name="t.txt",
                          snippet="Content", score_final=0.5)
            for i in range(5)
        ]
        
        fused_single = FusedContext(chunks=single_chunk, dense_count=1, sparse_count=0, graph_count=0)
        fused_multiple = FusedContext(chunks=multiple_chunks, dense_count=5, sparse_count=0, graph_count=0)
        
        _, score_single, _ = compute_confidence(fused_single, VerificationVerdict.APPROVE)
        _, score_multiple, _ = compute_confidence(fused_multiple, VerificationVerdict.APPROVE)
        
        assert score_multiple > score_single
    
    def test_confidence_level_thresholds(self):
        """Test confidence level threshold mapping."""
        # Create chunks that will give known scores
        chunks = [
            ChunkEvidence(chunk_id="c1", document_id="d1", file_name="t.txt",
                          snippet="Content", score_final=0.1)
        ]
        fused = FusedContext(chunks=chunks, dense_count=1, sparse_count=0, graph_count=0)
        
        level, score, _ = compute_confidence(fused, VerificationVerdict.APPROVE)
        
        # Verify level matches score according to thresholds
        if score >= 0.7:
            assert level == ConfidenceLevel.HIGH
        elif score >= 0.4:
            assert level == ConfidenceLevel.MEDIUM
        elif score >= 0.2:
            assert level == ConfidenceLevel.LOW
        else:
            assert level == ConfidenceLevel.NONE


class TestAbstentionResponse:
    """Test graceful abstention per ARCHITECTURE.md Section 5.4."""
    
    def test_abstention_includes_reason(self):
        """Abstention should explain why."""
        fused = FusedContext(chunks=[], dense_count=0, sparse_count=0, graph_count=0)
        response = _generate_abstention_response(
            "What is the budget?",
            fused,
            "No relevant sources found"
        )
        
        assert "don't have enough information" in response.lower()
        assert "No relevant sources found" in response
    
    def test_abstention_shows_partial_results(self):
        """Abstention should show partial results if available."""
        chunks = [
            ChunkEvidence(
                chunk_id="c1", document_id="d1", file_name="notes.txt",
                snippet="Some related content that might help",
                score_final=0.3,
            )
        ]
        fused = FusedContext(chunks=chunks, dense_count=1, sparse_count=0, graph_count=0)
        
        response = _generate_abstention_response(
            "What is the budget?",
            fused,
            "Low confidence"
        )
        
        assert "might be related" in response.lower()
        assert "Some related content" in response


class TestPromptBuilding:
    """Test prompt construction."""
    
    def test_reasoning_prompt_includes_context(self):
        """Reasoning prompt should include the context."""
        prompt = _build_reasoning_prompt(
            "What is the deadline?",
            "[Source 1]: The deadline is March 15."
        )
        
        assert "deadline" in prompt.lower()
        assert "[Source 1]" in prompt
        assert "March 15" in prompt
    
    def test_critic_prompt_includes_answer(self):
        """Critic prompt should include the answer to verify."""
        prompt = _build_critic_prompt(
            "What is the deadline?",
            "The deadline is March 15th.",
            "[Source 1]: The deadline is March 15."
        )
        
        assert "QUESTION" in prompt
        assert "ANSWER" in prompt
        assert "SOURCES" in prompt
        assert "March 15" in prompt


class TestIntegrationWithMocks:
    """Integration tests using mocked LLM calls."""
    
    @pytest.mark.asyncio
    async def test_reason_and_respond_empty_context(self):
        """Should abstain with empty context."""
        from backend.reasoning.cpumodel.llm_agent import reason_and_respond
        from backend.reasoning.cpumodel.models import QueryType, ModelTier
        
        fused = FusedContext(chunks=[], dense_count=0, sparse_count=0, graph_count=0)
        
        result = await reason_and_respond(
            query="What is the budget?",
            fused_context=fused,
            query_type=QueryType.SIMPLE,
            tier=ModelTier.T3,
        )
        
        assert result.confidence == ConfidenceLevel.NONE
        assert result.verification == VerificationVerdict.REJECT
        assert "don't have enough" in result.answer.lower()

