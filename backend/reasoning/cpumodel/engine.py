"""
Synapsis Reasoning Engine - Main Orchestrator
Ties together the full query → answer pipeline.

Pipeline:
1. Query Planner: Classify query type
2. Hybrid Retrieval: Dense + Sparse + Graph (based on query type)
3. RRF Fusion: Merge and rerank results
4. LLM Agent: Synthesize answer with citations
5. Critic: Verify answer
6. Response: Return AnswerPacket with confidence
"""
import logging
import time
from typing import Optional

from .models import (
    AnswerPacket, 
    ConfidenceLevel, 
    FusedContext, 
    ModelTier, 
    QueryType, 
    VerificationVerdict,
)
from .query_planner import plan_query
from .retrieval import hybrid_retrieve
from .fusion import fuse_results
from .llm_agent import reason_and_respond


logger = logging.getLogger(__name__)

# Input validation limits
MAX_QUERY_LENGTH = 4000  # Characters - beyond this truncate
MIN_QUERY_LENGTH = 1     # At least 1 char


def _validate_query(query: str) -> tuple[str, Optional[str]]:
    """
    Validate and sanitize user query.
    Returns: (sanitized_query, error_message_if_invalid)
    """
    if not query:
        return "", "Empty query"
    
    # Strip whitespace
    query = query.strip()
    
    if len(query) < MIN_QUERY_LENGTH:
        return "", "Query too short"
    
    # Truncate if too long (don't reject, just truncate)
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
        verification=VerificationVerdict.REJECT,
        query_type=QueryType.SIMPLE,
        model_used=tier,
        uncertainty_reason=error,
        latency_ms=0.0,
    )


async def process_query(
    query: str,
    tier: Optional[ModelTier] = None,
    top_k: int = 10,
) -> AnswerPacket:
    """
    Main entry point for the reasoning engine.
    Takes a user query and returns a grounded answer with citations.
    
    Args:
        query: The user's question
        tier: Model tier to use (defaults to T3 for CPU)
        top_k: Number of chunks to retrieve per path
    
    Returns:
        AnswerPacket with answer, sources, confidence, and verification
    """
    start_time = time.perf_counter()
    tier = tier or ModelTier.T3
    
    # Input validation
    query, error = _validate_query(query)
    if error:
        logger.warning(f"Query validation failed: {error}")
        return _create_error_response(error, tier)
    
    logger.info(f"Processing query: {query[:100]}...")
    
    # Step 1: Plan the query
    logger.info("Step 1: Query planning...")
    query_plan = await plan_query(query)
    logger.info(f"Query type: {query_plan.query_type.value}, entities: {query_plan.entities_detected}")
    
    # Step 2: Hybrid retrieval
    logger.info("Step 2: Hybrid retrieval...")
    retrieval_results = await hybrid_retrieve(
        query=query,
        query_type=query_plan.query_type,
        entities=query_plan.entities_detected,
        top_k=top_k,
    )
    
    # Step 3: Fuse results
    logger.info("Step 3: RRF fusion...")
    fused_context = fuse_results(retrieval_results, top_k=top_k)
    logger.info(f"Fused {len(fused_context.chunks)} chunks")
    
    # Step 4-6: Reason and respond (includes synthesis, verification, confidence)
    logger.info("Step 4-6: LLM reasoning + verification...")
    answer_packet = await reason_and_respond(
        query=query,
        fused_context=fused_context,
        query_type=query_plan.query_type,
        tier=tier,
    )
    
    total_latency = (time.perf_counter() - start_time) * 1000
    answer_packet.latency_ms = total_latency
    
    logger.info(
        f"Query processed in {total_latency:.0f}ms | "
        f"Confidence: {answer_packet.confidence.value} | "
        f"Verification: {answer_packet.verification.value}"
    )
    
    return answer_packet


class ReasoningEngine:
    """
    CPU-optimized reasoning engine using qwen2.5:0.5b (T3).
    
    This class provides the same interface as gpumodel.ReasoningEngine
    for easy swapping between CPU and GPU modes.
    
    Usage:
        engine = ReasoningEngine()
        result = await engine.process_query("What is the deadline?")
        print(result.answer)
    """
    
    def __init__(
        self,
        db_path: str = "data/synapsis.db",
        default_tier: ModelTier = ModelTier.T3,  # CPU uses T3
    ):
        self.db_path = db_path
        self.default_tier = default_tier
        # Lazy initialization of retriever
        self._retriever = None
    
    def _get_retriever(self):
        """Get or create the hybrid retriever."""
        if self._retriever is None:
            from .retrieval import HybridRetriever
            self._retriever = HybridRetriever(db_path=self.db_path)
        return self._retriever
    
    async def process_query(
        self,
        query: str,
        tier: Optional[ModelTier] = None,
        top_k: int = 10,
    ) -> AnswerPacket:
        """
        Process a query through the full reasoning pipeline.
        Wraps the module-level process_query for class-based usage.
        """
        return await process_query(query, tier=tier or self.default_tier, top_k=top_k)


# Module-level engine instance
_engine: Optional[ReasoningEngine] = None


def get_engine(
    db_path: str = "data/synapsis.db",
    force_new: bool = False,
) -> ReasoningEngine:
    """
    Get or create the CPU reasoning engine.
    
    Args:
        db_path: Path to SQLite database
        force_new: If True, create a new engine even if one exists
        
    Returns:
        Configured ReasoningEngine instance
    """
    global _engine
    
    if _engine is None or force_new:
        _engine = ReasoningEngine(db_path=db_path)
    
    return _engine


async def init_engine(db_path: str = "data/synapsis.db") -> ReasoningEngine:
    """
    Initialize the CPU reasoning engine.
    Pre-loads BM25 index and graph for faster first query.
    
    Call this during application startup:
        engine = await init_engine()
    """
    engine = get_engine(db_path, force_new=True)
    
    # Pre-load retriever components
    retriever = engine._get_retriever()
    
    # Trigger lazy loading of BM25 and graph
    logger.info("Pre-loading BM25 index...")
    await retriever.sparse._load_corpus()
    
    logger.info("Pre-loading graph...")
    await retriever.graph._load_graph()
    
    logger.info("CPU Reasoning Engine initialized")
    return engine


async def ask(query: str) -> AnswerPacket:
    """
    Convenience function - simple interface to ask a question.
    Uses default settings optimized for CPU.
    """
    return await process_query(query, tier=ModelTier.T3, top_k=10)

