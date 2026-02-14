"""
Synapsis Reasoning Engine
=========================
LLM-powered query understanding, retrieval, and grounded answer generation.

Components:
- ollama_client: 3-tier fallback LLM client (phi4-mini → qwen2.5:3b → qwen2.5:0.5b)
- query_planner: Classify queries into SIMPLE/MULTI_HOP/TEMPORAL
- retriever: Hybrid retrieval (dense + sparse + graph)
- fusion: RRF fusion to merge and rerank results
- reasoner: LLM synthesis with inline citations
- critic: Verify answers against sources (APPROVE/REVISE/REJECT)
- confidence: Calculate confidence scores
"""

from .ollama_client import OllamaClient
from .query_planner import QueryPlanner, QueryType
from .retriever import HybridRetriever, RetrievalResult
from .fusion import RRFFusion
from .reasoner import LLMReasoner, ReasoningResult
from .critic import CriticAgent, CriticVerdict
from .confidence import ConfidenceScorer, ConfidenceLevel

__all__ = [
    "OllamaClient",
    "QueryPlanner",
    "QueryType",
    "HybridRetriever",
    "RetrievalResult",
    "RRFFusion",
    "LLMReasoner",
    "ReasoningResult",
    "CriticAgent",
    "CriticVerdict",
    "ConfidenceScorer",
    "ConfidenceLevel",
]
