"""
Synapsis Reasoning Engine - CPU Model Implementation
Optimized for CPU-only operation using qwen2.5:0.5b (T3)

This is the CPU-optimized implementation. GPU implementation will be in gpumodel/.
"""

from .models import (
    AnswerPacket,
    ChunkEvidence,
    ConfidenceLevel,
    FusedContext,
    LLMResponse,
    ModelTier,
    QueryPlan,
    QueryType,
    RetrievalResult,
    VerificationVerdict,
)
from .engine import ask, process_query
from .ollama_client import get_ollama_client, OllamaClient
from .query_planner import plan_query, classify_query
from .retrieval import hybrid_retrieve, get_retriever, HybridRetriever
from .fusion import fuse_results, format_context_for_llm
from .llm_agent import reason_and_respond, synthesize_answer, verify_answer

__all__ = [
    # Main functions
    "ask",
    "process_query",
    "plan_query",
    "classify_query",
    "hybrid_retrieve",
    "fuse_results",
    "reason_and_respond",
    "synthesize_answer",
    "verify_answer",
    # Models
    "AnswerPacket",
    "ChunkEvidence",
    "ConfidenceLevel",
    "FusedContext",
    "LLMResponse",
    "ModelTier",
    "QueryPlan",
    "QueryType",
    "RetrievalResult",
    "VerificationVerdict",
    # Classes
    "get_ollama_client",
    "OllamaClient",
    "get_retriever",
    "HybridRetriever",
    "format_context_for_llm",
]
