"""
Synapsis Reasoning Engine - GPU Model Implementation
Optimized for GPU operation using phi4-mini (T1) as primary model.

This implementation leverages GPU acceleration for:
- Faster embedding generation (batch processing)
- Larger model support (phi4-mini 3.8B)
- Higher throughput with concurrent requests
- CUDA/MPS acceleration for inference
"""

from .ollama_client import OllamaClient, ModelTier, LLMResponse
from .query_planner import QueryPlanner, QueryPlan, QueryType
from .retriever import (
    HybridRetriever,
    DenseRetriever,
    SparseRetriever,
    GraphRetriever,
    RetrievalResult,
    RetrievalBundle,
)
from .fusion import RRFFusion, FusedResult, build_context_string
from .reasoner import LLMReasoner, ReasoningResult
from .critic import CriticAgent, CriticResult, CriticVerdict
from .confidence import ConfidenceScorer, ConfidenceResult, ConfidenceLevel
from .engine import ReasoningEngine, AnswerPacket, ask, process_query, get_engine, init_engine

__all__ = [
    # Main Entry Points
    "ask",
    "process_query",
    "get_engine",
    "init_engine",
    "ReasoningEngine",
    "AnswerPacket",
    # Ollama Client
    "OllamaClient",
    "ModelTier",
    "LLMResponse",
    # Query Planning
    "QueryPlanner",
    "QueryPlan",
    "QueryType",
    # Retrieval
    "HybridRetriever",
    "DenseRetriever",
    "SparseRetriever",
    "GraphRetriever",
    "RetrievalResult",
    "RetrievalBundle",
    # Fusion
    "RRFFusion",
    "FusedResult",
    "build_context_string",
    # Reasoning
    "LLMReasoner",
    "ReasoningResult",
    # Critic
    "CriticAgent",
    "CriticResult",
    "CriticVerdict",
    # Confidence
    "ConfidenceScorer",
    "ConfidenceResult",
    "ConfidenceLevel",
]
