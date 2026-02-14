"""
Synapsis Reasoning Engine
Grounded Q&A with hybrid retrieval, RRF fusion, and critic verification.

Structure:
- cpumodel/: CPU-optimized implementation (qwen2.5:0.5b default)
- gpumodel/: GPU-optimized implementation (phi4-mini default) [TODO: colleague]
- tests/: Test suite

Main entry points:
- ask(query): Simple interface for asking questions
- process_query(query, tier, top_k): Full control over query processing

Default: Uses CPU model. For GPU, import from reasoning.gpumodel directly.
"""

# Import from CPU model by default (our target: CPU-only operation)
from .cpumodel import (
    # Main functions
    ask,
    process_query,
    plan_query,
    classify_query,
    hybrid_retrieve,
    fuse_results,
    reason_and_respond,
    # Models
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
    # Classes
    get_ollama_client,
    OllamaClient,
    get_retriever,
    HybridRetriever,
)

__all__ = [
    # Main functions
    "ask",
    "process_query",
    "plan_query",
    "classify_query",
    "hybrid_retrieve",
    "fuse_results",
    "reason_and_respond",
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
]
