"""
Synapsis Reasoning Engine - GPU Main Orchestrator
Ties together the full query → answer pipeline using phi4-mini (T1).

Pipeline:
1. Query Planner: Classify query type
2. Hybrid Retrieval: Dense + Sparse + Graph (based on query type)
3. RRF Fusion: Merge and rerank results
4. LLM Reasoner: Synthesize answer with citations (Phi-4-mini 3.8B)
5. Critic Agent: Verify answer (Self-Verification)
6. Confidence Scorer: Calculate confidence
7. Response: Return AnswerPacket
"""
import logging
import time
from typing import Optional
from dataclasses import dataclass

from .ollama_client import OllamaClient, ModelTier
from .query_planner import QueryPlanner, QueryPlan, QueryType
from .retriever import HybridRetriever, RetrievalBundle
from .fusion import RRFFusion, FusedResult, build_context_string
from .reasoner import LLMReasoner, ReasoningResult
from .critic import CriticAgent, CriticVerdict, CriticResult
from .confidence import ConfidenceScorer, ConfidenceLevel, ConfidenceResult


logger = logging.getLogger(__name__)

# Input validation limits
MAX_QUERY_LENGTH = 4000
MIN_QUERY_LENGTH = 1


@dataclass
class AnswerPacket:
    """
    Final response structure - the contract with frontend.
    GPU mode with phi4-mini for best quality.
    """
    answer: str
    confidence: ConfidenceLevel
    confidence_score: float
    sources: list[FusedResult]
    verification: CriticVerdict
    query_type: QueryType
    model_used: ModelTier
    uncertainty_reason: Optional[str] = None
    reasoning_chain: Optional[str] = None
    latency_ms: float = 0.0
    gpu_accelerated: bool = True


def _validate_query(query: str) -> tuple[str, Optional[str]]:
    """Validate and sanitize user query."""
    if not query:
        return "", "Empty query"
    
    query = query.strip()
    
    if len(query) < MIN_QUERY_LENGTH:
        return "", "Query too short"
    
    if len(query) > MAX_QUERY_LENGTH:
        logger.warning(f"Query truncated from {len(query)} to {MAX_QUERY_LENGTH} chars")
        query = query[:MAX_QUERY_LENGTH]
    
    return query, None


def _create_error_response(error: str, tier: ModelTier) -> AnswerPacket:
    """Create an error response for invalid queries."""
    return AnswerPacket(
        answer=f"I couldn't process your request: {error}",
        confidence=ConfidenceLevel.NONE,
        confidence_score=0.0,
        sources=[],
        verification=CriticVerdict.REJECT,
        query_type=QueryType.SIMPLE,
        model_used=tier,
        uncertainty_reason=error,
        latency_ms=0.0,
    )


def _generate_abstention_response(
    query: str,
    sources: list[FusedResult],
    reason: str,
) -> str:
    """Generate a graceful abstention response with partial results."""
    response = f"I don't have enough information in your documents to answer this confidently.\n\n"
    response += f"Reason: {reason}\n\n"
    
    if sources:
        response += "Here's what I found that might be related:\n\n"
        for i, src in enumerate(sources[:3], start=1):
            snippet = src.content[:200] + "..." if len(src.content) > 200 else src.content
            file_info = f" ({src.citation_label})" if src.source_file else ""
            response += f"- [Source {i}]{file_info}: {snippet}\n\n"
    
    return response


class ReasoningEngine:
    """
    GPU-optimized reasoning engine using Phi-4-mini (T1).
    
    Usage:
        engine = ReasoningEngine(qdrant_client=qdrant, sqlite_path="data/knowledge.db")
        result = await engine.process_query("What is the deadline?")
        print(result.answer)
    """
    
    def __init__(
        self,
        qdrant_client=None,
        qdrant_collection: str = "chunks",
        sqlite_path: Optional[str] = None,
        default_tier: ModelTier = ModelTier.T1,  # GPU uses T1
    ):
        self.ollama = OllamaClient(default_tier=default_tier)
        self.query_planner = QueryPlanner(self.ollama)
        self.retriever = HybridRetriever(
            qdrant_client=qdrant_client,
            collection_name=qdrant_collection,
            sqlite_path=sqlite_path,
        )
        self.fusion = RRFFusion(k=60, recency_weight=0.2)
        self.reasoner = LLMReasoner(self.ollama, max_context_chars=8000)  # GPU allows more context
        self.critic = CriticAgent(self.ollama, max_context_chars=6000)
        self.confidence_scorer = ConfidenceScorer()
        self.default_tier = default_tier
    
    async def process_query(
        self,
        query: str,
        tier: Optional[ModelTier] = None,
        top_k: int = 15,  # Higher for GPU
    ) -> AnswerPacket:
        """
        Main entry point for the GPU reasoning engine.
        Takes a user query and returns a grounded answer with citations.
        """
        start_time = time.perf_counter()
        tier = tier or self.default_tier
        
        # Input validation
        query, error = _validate_query(query)
        if error:
            logger.warning(f"Query validation failed: {error}")
            return _create_error_response(error, tier)
        
        logger.info(f"GPU Processing query: {query[:100]}... (tier: {tier.name})")
        
        # Step 1: Plan the query
        logger.info("Step 1: Query planning...")
        query_plan = await self.query_planner.plan(query)
        logger.info(f"Query type: {query_plan.query_type.value}, entities: {query_plan.entities_mentioned}")
        
        # Step 2: Hybrid retrieval
        logger.info("Step 2: Hybrid retrieval...")
        retrieval_bundle = await self.retriever.retrieve(
            query=query,
            query_type=query_plan.query_type,
            entities=query_plan.entities_mentioned,
            top_k=top_k,
        )
        
        # Step 3: Fuse results
        logger.info("Step 3: RRF fusion...")
        fused_results = self.fusion.fuse(retrieval_bundle, top_k=top_k)
        logger.info(f"Fused {len(fused_results)} chunks")
        
        # Check if we have any results
        if not fused_results:
            return AnswerPacket(
                answer=_generate_abstention_response(query, [], "No relevant sources found"),
                confidence=ConfidenceLevel.NONE,
                confidence_score=0.0,
                sources=[],
                verification=CriticVerdict.REJECT,
                query_type=query_plan.query_type,
                model_used=tier,
                uncertainty_reason="No relevant sources found",
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )
        
        # Step 4: LLM Reasoning (Phi-4-mini)
        logger.info("Step 4: LLM reasoning with Phi-4-mini...")
        reasoning_result = await self.reasoner.reason(
            question=query,
            sources=fused_results,
            tier=tier,
        )
        
        # Handle abstention
        if reasoning_result.abstained:
            return AnswerPacket(
                answer=_generate_abstention_response(query, fused_results, reasoning_result.abstention_reason or "Insufficient information"),
                confidence=ConfidenceLevel.NONE,
                confidence_score=0.0,
                sources=fused_results,
                verification=CriticVerdict.REJECT,
                query_type=query_plan.query_type,
                model_used=tier,
                uncertainty_reason=reasoning_result.abstention_reason,
                latency_ms=(time.perf_counter() - start_time) * 1000,
            )
        
        # Step 5: Critic verification (Self-Verification)
        logger.info("Step 5: Critic agent self-verification...")
        critic_result = await self.critic.verify(
            question=query,
            answer=reasoning_result.answer,
            sources=fused_results,
            tier=tier,
        )
        
        # Step 6: Confidence scoring
        logger.info("Step 6: Confidence scoring...")
        confidence_result = self.confidence_scorer.calculate(
            retrieval_results=fused_results,
            reasoning_result=reasoning_result,
            critic_result=critic_result,
        )
        
        # Handle rejection
        final_answer = reasoning_result.answer
        if critic_result.verdict == CriticVerdict.REJECT or confidence_result.should_abstain:
            final_answer = _generate_abstention_response(
                query,
                fused_results,
                confidence_result.reasoning or "Answer could not be verified"
            )
        
        total_latency = (time.perf_counter() - start_time) * 1000
        
        logger.info(
            f"GPU Query processed in {total_latency:.0f}ms | "
            f"Confidence: {confidence_result.level.value} ({confidence_result.score:.2f}) | "
            f"Verification: {critic_result.verdict.value}"
        )
        
        return AnswerPacket(
            answer=final_answer,
            confidence=confidence_result.level,
            confidence_score=confidence_result.score,
            sources=fused_results,
            verification=critic_result.verdict,
            query_type=query_plan.query_type,
            model_used=tier,
            uncertainty_reason=confidence_result.reasoning if confidence_result.level in [ConfidenceLevel.LOW, ConfidenceLevel.NONE] else None,
            reasoning_chain=reasoning_result.reasoning_chain,
            latency_ms=total_latency,
        )


# Module-level engine instance
_engine: Optional[ReasoningEngine] = None


def get_engine(
    qdrant_client=None,
    sqlite_path: Optional[str] = None,
    force_new: bool = False,
) -> ReasoningEngine:
    """
    Get or create the GPU reasoning engine.
    
    Args:
        qdrant_client: Qdrant client instance (optional, will create default if None)
        sqlite_path: Path to SQLite database for graph data (optional)
        force_new: If True, create a new engine even if one exists
        
    Returns:
        Configured ReasoningEngine instance
    """
    global _engine
    
    if _engine is None or force_new:
        # Try to get Qdrant client from existing services if not provided
        if qdrant_client is None:
            try:
                from backend.services.qdrant_service import get_qdrant_client
                qdrant_client = get_qdrant_client()
            except ImportError:
                logger.warning("Qdrant service not available, dense retrieval disabled")
        
        # Try to get SQLite path from config if not provided
        if sqlite_path is None:
            try:
                from backend.config import settings
                sqlite_path = getattr(settings, 'SQLITE_PATH', None)
            except ImportError:
                pass
        
        _engine = ReasoningEngine(
            qdrant_client=qdrant_client,
            sqlite_path=sqlite_path,
        )
    
    return _engine


async def init_engine(
    qdrant_client=None,
    sqlite_path: Optional[str] = None,
) -> ReasoningEngine:
    """
    Initialize the engine with proper service connections.
    Syncs BM25 index from Qdrant on startup.
    
    Call this during application startup:
        engine = await init_engine()
    """
    engine = get_engine(qdrant_client, sqlite_path, force_new=True)
    
    # Sync BM25 from Qdrant
    if engine.retriever.qdrant_client:
        doc_count = await engine.retriever.sync_bm25_from_qdrant()
        logger.info(f"BM25 index synced with {doc_count} documents")
    
    return engine


async def process_query(
    query: str,
    tier: Optional[ModelTier] = None,
    top_k: int = 15,
) -> AnswerPacket:
    """Convenience function for processing queries with GPU engine."""
    engine = get_engine()
    return await engine.process_query(query, tier=tier, top_k=top_k)


async def ask(query: str) -> AnswerPacket:
    """
    Simple interface to ask a question.
    Uses GPU defaults (T1, higher top_k).
    """
    return await process_query(query, tier=ModelTier.T1, top_k=15)
