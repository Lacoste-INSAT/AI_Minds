"""
Tests for data models.
Validates that all models are correctly structured and have proper defaults.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from reasoning.cpumodel.models import (
    QueryType,
    ConfidenceLevel,
    VerificationVerdict,
    ModelTier,
    ChunkEvidence,
    QueryPlan,
    RetrievalResult,
    FusedContext,
    AnswerPacket,
    LLMResponse,
)


class TestEnums:
    """Test enum values match architecture spec."""
    
    def test_query_type_values(self):
        """Query types must match ARCHITECTURE.md Section 5.1."""
        assert QueryType.SIMPLE.value == "SIMPLE"
        assert QueryType.MULTI_HOP.value == "MULTI_HOP"
        assert QueryType.TEMPORAL.value == "TEMPORAL"
        assert QueryType.CONTRADICTION.value == "CONTRADICTION"
    
    def test_confidence_levels(self):
        """Confidence levels must match ARCHITECTURE.md Section 5.3."""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.NONE.value == "none"
    
    def test_verification_verdicts(self):
        """Critic verdicts must match ARCHITECTURE.md Section 5.1."""
        assert VerificationVerdict.APPROVE.value == "APPROVE"
        assert VerificationVerdict.REVISE.value == "REVISE"
        assert VerificationVerdict.REJECT.value == "REJECT"
    
    def test_model_tiers(self):
        """Model tiers must match ARCHITECTURE.md Section 10.2."""
        assert ModelTier.T1.value == "phi4-mini"      # 3.8B
        assert ModelTier.T2.value == "qwen2.5:3b"     # 3.1B
        assert ModelTier.T3.value == "qwen2.5:0.5b"   # 0.5B - CPU target


class TestChunkEvidence:
    """Test ChunkEvidence model."""
    
    def test_required_fields(self):
        """Must have chunk_id, document_id, file_name, snippet."""
        chunk = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="test.txt",
            snippet="Test content",
        )
        assert chunk.chunk_id == "c1"
        assert chunk.document_id == "d1"
        assert chunk.file_name == "test.txt"
        assert chunk.snippet == "Test content"
    
    def test_default_scores(self):
        """Scores should default to 0.0."""
        chunk = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="test.txt",
            snippet="Test",
        )
        assert chunk.score_dense == 0.0
        assert chunk.score_sparse == 0.0
        assert chunk.score_graph == 0.0
        assert chunk.score_final == 0.0
    
    def test_optional_page_number(self):
        """page_number should be optional."""
        chunk = ChunkEvidence(
            chunk_id="c1",
            document_id="d1",
            file_name="test.txt",
            snippet="Test",
        )
        assert chunk.page_number is None


class TestAnswerPacket:
    """Test AnswerPacket - the main response contract."""
    
    def test_required_fields_present(self):
        """AnswerPacket must include all mandatory fields per ARCHITECTURE.md."""
        packet = AnswerPacket(
            answer="Test answer",
            confidence=ConfidenceLevel.HIGH,
            confidence_score=0.85,
            sources=[],
            verification=VerificationVerdict.APPROVE,
            query_type=QueryType.SIMPLE,
            model_used=ModelTier.T3,
        )
        
        # These are MANDATORY per Section 9.3
        assert packet.answer is not None
        assert packet.confidence is not None
        assert packet.confidence_score is not None
        assert packet.sources is not None
        assert packet.verification is not None
    
    def test_optional_fields_can_be_none(self):
        """Optional fields should allow None."""
        packet = AnswerPacket(
            answer="Test",
            confidence=ConfidenceLevel.MEDIUM,
            confidence_score=0.5,
            sources=[],
            verification=VerificationVerdict.APPROVE,
            query_type=QueryType.SIMPLE,
            model_used=ModelTier.T3,
        )
        assert packet.uncertainty_reason is None
        assert packet.reasoning_chain is None


class TestQueryPlan:
    """Test QueryPlan model."""
    
    def test_basic_creation(self):
        """QueryPlan should store classification results."""
        plan = QueryPlan(
            query_type=QueryType.MULTI_HOP,
            original_query="What did John say about the project?",
            entities_detected=["John"],
            reasoning="Contains 'John said about' pattern",
        )
        assert plan.query_type == QueryType.MULTI_HOP
        assert "John" in plan.entities_detected


class TestLLMResponse:
    """Test LLMResponse model."""
    
    def test_success_response(self):
        """Successful response should have content and success=True."""
        response = LLMResponse(
            content="Generated text",
            model="qwen2.5:0.5b",
            success=True,
        )
        assert response.success is True
        assert response.content == "Generated text"
        assert response.error is None
    
    def test_error_response(self):
        """Error response should have success=False and error message."""
        response = LLMResponse(
            content="",
            model="qwen2.5:0.5b",
            success=False,
            error="Connection timeout",
        )
        assert response.success is False
        assert response.error == "Connection timeout"
