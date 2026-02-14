"""
Pytest fixtures for reasoning engine tests.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from reasoning.reasoning.cpumodel.models import (
    ChunkEvidence,
    QueryType,
    ModelTier,
    ConfidenceLevel,
    VerificationVerdict,
    RetrievalResult,
    FusedContext,
    LLMResponse,
)


@pytest.fixture
def sample_chunks():
    """Sample chunk evidence for testing."""
    return [
        ChunkEvidence(
            chunk_id="chunk_001",
            document_id="doc_001",
            file_name="meeting_notes.txt",
            snippet="The project deadline is March 15th. John confirmed this in the standup.",
            page_number=1,
            score_dense=0.85,
            score_sparse=0.0,
            score_graph=0.0,
        ),
        ChunkEvidence(
            chunk_id="chunk_002",
            document_id="doc_002",
            file_name="email_sarah.txt",
            snippet="Sarah mentioned the budget is $50,000 for Q2 marketing.",
            page_number=None,
            score_dense=0.72,
            score_sparse=0.65,
            score_graph=0.0,
        ),
        ChunkEvidence(
            chunk_id="chunk_003",
            document_id="doc_001",
            file_name="meeting_notes.txt",
            snippet="The team agreed to use React for the frontend redesign.",
            page_number=2,
            score_dense=0.68,
            score_sparse=0.0,
            score_graph=0.5,
        ),
    ]


@pytest.fixture
def sample_retrieval_results(sample_chunks):
    """Sample retrieval results from all three paths."""
    return {
        "dense": RetrievalResult(
            chunks=[sample_chunks[0], sample_chunks[1]],
            retrieval_type="dense",
            latency_ms=150.0,
        ),
        "sparse": RetrievalResult(
            chunks=[sample_chunks[1]],
            retrieval_type="sparse",
            latency_ms=50.0,
        ),
        "graph": RetrievalResult(
            chunks=[sample_chunks[2]],
            retrieval_type="graph",
            latency_ms=30.0,
        ),
    }


@pytest.fixture
def sample_fused_context(sample_chunks):
    """Sample fused context after RRF."""
    for i, chunk in enumerate(sample_chunks):
        chunk.score_final = 0.5 - (i * 0.1)  # Decreasing scores
    return FusedContext(
        chunks=sample_chunks,
        dense_count=2,
        sparse_count=1,
        graph_count=1,
        fusion_latency_ms=5.0,
    )


@pytest.fixture
def mock_ollama_response():
    """Mock successful Ollama response."""
    return LLMResponse(
        content="The project deadline is March 15th [Source 1].",
        model="qwen2.5:0.5b",
        prompt_tokens=100,
        completion_tokens=20,
        latency_ms=500.0,
        success=True,
        error=None,
    )


@pytest.fixture
def mock_ollama_client(mock_ollama_response):
    """Mock Ollama client for testing without actual LLM calls."""
    with patch("backend.reasoning.cpumodel.ollama_client.httpx.AsyncClient") as mock:
        client_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = client_instance
        
        # Mock health check
        health_response = MagicMock()
        health_response.status_code = 200
        health_response.json.return_value = {
            "models": [
                {"name": "qwen2.5:0.5b"},
                {"name": "qwen2.5:3b"},
            ]
        }
        client_instance.get.return_value = health_response
        
        # Mock generate
        gen_response = MagicMock()
        gen_response.status_code = 200
        gen_response.json.return_value = {
            "message": {"content": mock_ollama_response.content},
            "prompt_eval_count": 100,
            "eval_count": 20,
        }
        gen_response.raise_for_status = MagicMock()
        client_instance.post.return_value = gen_response
        
        yield mock
