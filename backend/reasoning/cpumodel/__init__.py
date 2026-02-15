"""
Synapsis Reasoning Engine - CPU Model Implementation
Optimized for CPU-only operation using qwen2.5:0.5b (T3)

This is the CPU-optimized implementation with the same 6-component pipeline:
1. Intent Detector (QueryPlanner) - query_planner.py
2. Hybrid Retriever (Dense+Sparse+Graph) - retrieval.py
3. Context Assembler (RRF Fusion) - fusion.py
4. LLM Reasoner - llm_agent.py
5. Self Verification (Critic) - llm_agent.py
6. Confidence Scorer - llm_agent.py
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
from .engine import (
    ask, 
    process_query, 
    get_engine, 
    init_engine,
    ReasoningEngine,
)
from .ollama_client import get_ollama_client, OllamaClient
from .query_planner import plan_query, classify_query
from .retrieval import hybrid_retrieve, get_retriever, HybridRetriever
from .fusion import fuse_results, format_context_for_llm
from .llm_agent import (
    reason_and_respond, 
    synthesize_answer, 
    verify_answer,
    compute_confidence,
)

__all__ = [
    # Main Entry Points
    "ask",
    "process_query",
    "get_engine",
    "init_engine",
    "ReasoningEngine",
    # Query Planning (Intent Detector)
    "plan_query",
    "classify_query",
    # Retrieval (Hybrid Retriever)
    "hybrid_retrieve",
    "get_retriever",
    "HybridRetriever",
    # Fusion (Context Assembler)
    "fuse_results",
    "format_context_for_llm",
    # LLM Agent (Reasoner + Critic + Confidence)
    "reason_and_respond",
    "synthesize_answer",
    "verify_answer",
    "compute_confidence",
    # Data Models
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
    # Client Classes
    "get_ollama_client",
    "OllamaClient",
]
