"""
Synapsis Reasoning Engine - FastAPI Router
==========================================

API endpoints for the LLM reasoning pipeline.

Endpoints:
- POST /query/ask    → Full reasoning pipeline
- GET  /query/health → Health check for reasoning services

Supports both GPU (phi4-mini) and CPU (qwen2.5:0.5b) modes.

Usage:
    from backend.reasoning.api import router
    app.include_router(router, prefix="/query", tags=["reasoning"])
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum
import logging
import time

# Import both model implementations
from backend.reasoning.cpumodel.models import (
    ModelTier as CPUModelTier,
    ConfidenceLevel as CPUConfidenceLevel,
    VerificationVerdict,
    AnswerPacket as CPUAnswerPacket,
)
from backend.reasoning.cpumodel.engine import process_query as cpu_process_query
from backend.reasoning.cpumodel.ollama_client import get_ollama_client, DEFAULT_TIER

from backend.reasoning.gpumodel.engine import process_query as gpu_process_query
from backend.reasoning.gpumodel.ollama_client import ModelTier as GPUModelTier
from backend.reasoning.gpumodel.confidence import ConfidenceLevel as GPUConfidenceLevel
from backend.reasoning.gpumodel.critic import CriticVerdict


class ExecutionMode(str, Enum):
    """Execution mode for the reasoning engine."""
    GPU = "gpu"  # phi4-mini (T1) → best quality, requires GPU/fast CPU
    CPU = "cpu"  # qwen2.5:0.5b (T3) → lightweight, runs on any CPU

logger = logging.getLogger(__name__)

# =============================================================================
# Request / Response Models
# =============================================================================

class QueryRequest(BaseModel):
    """
    Request body for POST /query/ask
    
    Example:
        {
            "query": "What did John say about the project deadline?",
            "mode": "gpu",
            "tier": "T1"
        }
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="The user's question (1-4000 chars)",
        json_schema_extra={"example": "What is the project deadline?"}
    )
    mode: Optional[str] = Field(
        default="gpu",
        description="Execution mode: 'gpu' (phi4-mini, best quality) or 'cpu' (qwen2.5:0.5b, lightweight)",
        json_schema_extra={"example": "gpu"}
    )
    tier: Optional[str] = Field(
        default=None,
        description="Model tier: T1 (phi4-mini), T2 (qwen2.5:3b), T3 (qwen2.5:0.5b). Default: T1 for GPU, T3 for CPU",
        json_schema_extra={"example": "T1"}
    )


class SourceInfo(BaseModel):
    """Information about a source used in the answer."""
    chunk_id: str
    file_name: str
    snippet: str = Field(description="Relevant text excerpt")
    score: float = Field(description="Relevance score (0-1)")
    page_number: Optional[int] = None


class QueryResponse(BaseModel):
    """
    Response body for POST /query/ask
    
    Per Section 9.3: Every response MUST include sources[], confidence, verification
    """
    answer: str = Field(description="The generated answer (or abstention message)")
    confidence: str = Field(description="Confidence level: high, medium, low, none")
    confidence_score: float = Field(description="Raw confidence score (0-1)")
    verification: str = Field(description="Critic verdict: APPROVE, REVISE, REJECT")
    sources: list[SourceInfo] = Field(
        default_factory=list,
        description="Evidence chunks used (may be empty on abstention)"
    )
    query_type: str = Field(description="Query classification: SIMPLE, MULTI_HOP, TEMPORAL, etc.")
    model_used: str = Field(description="Which model tier was used: T1, T2, T3")
    mode: str = Field(description="Execution mode: gpu or cpu")
    latency_ms: float = Field(description="Total processing time in milliseconds")
    reasoning_chain: Optional[str] = Field(
        default=None,
        description="Reasoning steps (if available)"
    )


class HealthResponse(BaseModel):
    """Response body for GET /query/health"""
    status: str = Field(description="Overall status: healthy, degraded, unhealthy")
    ollama: bool = Field(description="Ollama reachable")
    model_available: Optional[str] = Field(description="Best available model tier")
    message: Optional[str] = Field(default=None, description="Additional info")


# =============================================================================
# Router
# =============================================================================

router = APIRouter()


@router.post(
    "/ask",
    response_model=QueryResponse,
    summary="Ask a question",
    description="Full reasoning pipeline: classify → retrieve → fuse → synthesize → verify",
    responses={
        200: {"description": "Answer generated successfully"},
        400: {"description": "Invalid query"},
        503: {"description": "LLM service unavailable"},
    }
)
async def ask_question(request: QueryRequest) -> QueryResponse:
    """
    Process a user question through the full reasoning pipeline.
    
    Pipeline steps (6 components from diagram):
    1. Intent Detector - Query classification (SIMPLE, MULTI_HOP, TEMPORAL, etc.)
    2. Hybrid Retriever - Dense + Sparse + Graph retrieval
    3. Context Assembler - RRF fusion with deduplication
    4. LLM Reasoner - Generate grounded answer (Phi-4-mini / TinyLlama)
    5. Self Verification - Critic agent validates against sources
    6. Confidence Scorer - Calculate confidence and uncertainty
    
    Returns abstention if evidence is insufficient.
    """
    start_time = time.perf_counter()
    
    # Determine execution mode
    mode = (request.mode or "gpu").lower()
    use_gpu = mode != "cpu"
    
    try:
        if use_gpu:
            # GPU mode - use phi4-mini (T1) as default
            tier_map = {"T1": GPUModelTier.T1, "T2": GPUModelTier.T2, "T3": GPUModelTier.T3}
            tier = tier_map.get(request.tier.upper(), GPUModelTier.T1) if request.tier else GPUModelTier.T1
            
            result = await gpu_process_query(
                query=request.query,
                tier=tier,
                top_k=15,  # GPU allows higher top_k
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Map GPU sources to response format
            sources = []
            if result.sources:
                for src in result.sources:
                    sources.append(SourceInfo(
                        chunk_id=src.chunk_id,
                        file_name=src.source_file.split("/")[-1].split("\\")[-1],
                        snippet=src.content[:500],  # Truncate for response
                        score=src.fused_score,
                        page_number=src.metadata.get("page_number"),
                    ))
            
            return QueryResponse(
                answer=result.answer,
                confidence=result.confidence.value if result.confidence else "none",
                confidence_score=result.confidence_score,
                verification=result.verification.value.upper() if result.verification else "REVISE",
                sources=sources,
                query_type=result.query_type.value if result.query_type else "SIMPLE",
                model_used=result.model_used.name if result.model_used else "T1",
                mode="gpu",
                latency_ms=elapsed_ms,
                reasoning_chain=result.reasoning_chain,
            )
        
        else:
            # CPU mode - use qwen2.5:0.5b (T3) as default
            tier_map = {"T1": CPUModelTier.T1, "T2": CPUModelTier.T2, "T3": CPUModelTier.T3}
            tier = tier_map.get(request.tier.upper(), DEFAULT_TIER) if request.tier else DEFAULT_TIER
            
            result = await cpu_process_query(
                query=request.query,
                tier=tier,
            )
            
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            
            # Map CPU sources to response format
            sources = []
            if result.sources:
                for src in result.sources:
                    sources.append(SourceInfo(
                        chunk_id=src.chunk_id,
                        file_name=src.file_name,
                        snippet=src.snippet[:500],  # Truncate for response
                        score=src.score_final,
                        page_number=src.page_number,
                    ))
            
            return QueryResponse(
                answer=result.answer,
                confidence=result.confidence.value if result.confidence else "none",
                confidence_score=result.confidence_score,
                verification=result.verification.value if result.verification else "REVISE",
                sources=sources,
                query_type=result.query_type.value if result.query_type else "SIMPLE",
                model_used=result.model_used.value if result.model_used else "qwen2.5:0.5b",
                mode="cpu",
                latency_ms=elapsed_ms,
                reasoning_chain=result.reasoning_chain,
            )
        
    except ValueError as e:
        # Input validation errors
        logger.warning(f"Invalid query: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Reasoning service temporarily unavailable"
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the reasoning engine and Ollama are operational",
)
async def check_health() -> HealthResponse:
    """
    Health check for the reasoning engine.
    
    Checks:
    - Ollama API reachability
    - Model availability
    """
    try:
        client = get_ollama_client()
        health = await client.health_check()
        
        if health.get("status") == "up":
            # Determine best available tier
            if health.get("t1_available"):
                tier = "T1"
            elif health.get("t2_available"):
                tier = "T2"
            elif health.get("t3_available"):
                tier = "T3"
            else:
                tier = None
            return HealthResponse(
                status="healthy",
                ollama=True,
                model_available=tier,
                message=f"Using model tier {tier}" if tier else "Ollama ready",
            )
        else:
            return HealthResponse(
                status="degraded",
                ollama=False,
                model_available=None,
                message="Ollama not reachable - LLM features unavailable",
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            ollama=False,
            model_available=None,
            message=str(e),
        )


# =============================================================================
# Main Application Factory (for standalone testing)
# =============================================================================

def create_app():
    """
    Create FastAPI app for standalone testing.
    
    Usage:
        uvicorn backend.reasoning.api:create_app --factory --reload
    
    Or import the router into the main app:
        from backend.reasoning.api import router
        app.include_router(router, prefix="/query", tags=["reasoning"])
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    
    app = FastAPI(
        title="Synapsis Reasoning Engine",
        description="LLM-powered personal knowledge assistant",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include reasoning router
    app.include_router(router, prefix="/query", tags=["reasoning"])
    
    # Root health check
    @app.get("/health")
    async def root_health():
        return {"status": "ok", "service": "synapsis-reasoning"}
    
    return app


# For running directly: uvicorn backend.reasoning.api:app --reload
app = create_app()
