"""
Synapsis Reasoning Engine - Data Models
Core data structures for the query/response pipeline.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class QueryType(str, Enum):
    """Classification of user query types for routing."""
    SIMPLE = "SIMPLE"           # Direct lookup: "What is X?"
    MULTI_HOP = "MULTI_HOP"     # Graph traversal: "Ideas from Y about X"
    TEMPORAL = "TEMPORAL"       # Timeline: "How did my view change?"
    CONTRADICTION = "CONTRADICTION"  # Belief diff: "Did I say conflicting things?"


class ConfidenceLevel(str, Enum):
    """Confidence levels for answer grounding."""
    HIGH = "high"       # >= 0.7
    MEDIUM = "medium"   # >= 0.4
    LOW = "low"         # >= 0.2
    NONE = "none"       # < 0.2 -> triggers abstention


class VerificationVerdict(str, Enum):
    """Critic agent verification outcomes."""
    APPROVE = "APPROVE"   # Answer fully supported by sources
    REVISE = "REVISE"     # Partially supported, needs retry
    REJECT = "REJECT"     # Fabricated/unsupported -> abstain


class ModelTier(str, Enum):
    """3-tier fallback model chain for CPU-only operation."""
    T1 = "phi4-mini"        # 3.8B - primary (may be too slow on CPU)
    T2 = "qwen2.5:3b"       # 3.1B - fallback
    T3 = "qwen2.5:0.5b"     # 0.5B - low-end CPU (our target)


@dataclass
class ChunkEvidence:
    """A retrieved chunk used as evidence for an answer."""
    chunk_id: str
    document_id: str
    file_name: str
    snippet: str            # The actual text content
    page_number: Optional[int] = None
    score_dense: float = 0.0    # Qdrant similarity score
    score_sparse: float = 0.0   # BM25 score
    score_graph: float = 0.0    # Graph traversal score
    score_final: float = 0.0    # After RRF fusion


@dataclass
class QueryPlan:
    """Output of the Query Planner - routing decision."""
    query_type: QueryType
    original_query: str
    rewritten_query: Optional[str] = None  # Optionally improved query
    entities_detected: list[str] = field(default_factory=list)
    reasoning: str = ""  # Why this classification


@dataclass
class RetrievalResult:
    """Output from a single retrieval path (dense/sparse/graph)."""
    chunks: list[ChunkEvidence]
    retrieval_type: str  # "dense" | "sparse" | "graph"
    latency_ms: float = 0.0


@dataclass
class FusedContext:
    """Merged and reranked results from all retrieval paths."""
    chunks: list[ChunkEvidence]  # Deduplicated, reranked
    dense_count: int = 0
    sparse_count: int = 0
    graph_count: int = 0
    fusion_latency_ms: float = 0.0


@dataclass
class AnswerPacket:
    """
    Final response structure - the contract with frontend.
    Every field except reasoning_chain is MANDATORY.
    """
    answer: str
    confidence: ConfidenceLevel
    confidence_score: float
    sources: list[ChunkEvidence]
    verification: VerificationVerdict
    query_type: QueryType
    model_used: ModelTier
    uncertainty_reason: Optional[str] = None  # Why low confidence
    reasoning_chain: Optional[str] = None     # Transparency
    latency_ms: float = 0.0


@dataclass
class LLMResponse:
    """Raw response from Ollama."""
    content: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None
