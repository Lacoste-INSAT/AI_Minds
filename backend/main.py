"""
Synapsis Backend - FastAPI Application

Main entry point for the Synapsis personal knowledge system backend.
Exposes the reasoning pipeline via REST API.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import json
import asyncio
import structlog

from backend.reasoning.critic import ReasoningPipeline
from backend.reasoning.ollama_client import OllamaClient
from backend.reasoning.confidence import ConfidenceLevel
from backend.database import memory_db

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Synapsis API",
    description="Personal knowledge system with AI reasoning",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - localhost only (air-gapped)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
reasoning_pipeline: Optional[ReasoningPipeline] = None
ollama_client: Optional[OllamaClient] = None


# =============================================================================
# Request/Response Models
# =============================================================================

class AskRequest(BaseModel):
    """Request body for /query/ask endpoint"""
    query: str = Field(..., min_length=1, max_length=2000, description="User question")
    include_reasoning: bool = Field(default=True, description="Include reasoning chain in response")
    max_sources: int = Field(default=5, ge=1, le=20, description="Maximum number of sources to return")


class SourceItem(BaseModel):
    """A single source citation"""
    id: str
    title: str
    snippet: str
    relevance_score: float
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None


class AnswerResponse(BaseModel):
    """Response body for /query/ask endpoint"""
    answer: str
    confidence: str  # HIGH, MEDIUM, LOW, NONE
    confidence_score: float
    verification: str  # APPROVE, REVISE, REJECT
    sources: List[SourceItem]
    reasoning_chain: Optional[str] = None
    query_type: str  # SIMPLE, MULTI_HOP, TEMPORAL, CONTRADICTION, AGGREGATION
    model_used: str
    latency_ms: int


class HealthResponse(BaseModel):
    """Response body for /health endpoint"""
    status: str
    ollama_healthy: bool
    qdrant_healthy: bool
    sqlite_healthy: bool
    models_available: List[str]
    timestamp: datetime


class MemoryItem(BaseModel):
    """A single memory/knowledge item"""
    id: str
    title: str
    content: str
    source_type: str  # document, note, meeting, etc.
    file_path: str
    created_at: datetime
    modified_at: datetime
    entities: List[str]
    tags: List[str]


class MemoryTimelineResponse(BaseModel):
    """Response for /memory/timeline"""
    items: List[MemoryItem]
    total_count: int
    page: int
    page_size: int


class GraphNode(BaseModel):
    """Node in the knowledge graph"""
    id: str
    label: str
    type: str  # person, project, concept, document
    properties: dict


class GraphEdge(BaseModel):
    """Edge in the knowledge graph"""
    source: str
    target: str
    relationship: str
    weight: float


class GraphResponse(BaseModel):
    """Response for /memory/graph"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class StatsResponse(BaseModel):
    """Response for /memory/stats"""
    total_documents: int
    total_entities: int
    total_relationships: int
    documents_by_type: dict
    recent_ingestions: int
    storage_used_mb: float


class ConfigSources(BaseModel):
    """Configuration for watched directories"""
    watched_directories: List[str]
    exclusion_patterns: List[str]
    file_types: List[str]


class IngestionStatus(BaseModel):
    """Status of the ingestion pipeline"""
    is_running: bool
    queue_depth: int
    last_scan_time: Optional[datetime]
    files_processed_today: int
    errors_today: int


class DigestItem(BaseModel):
    """A single insight from the proactive engine"""
    id: str
    type: str  # pattern, contradiction, reminder, summary
    title: str
    description: str
    related_documents: List[str]
    generated_at: datetime


class DigestResponse(BaseModel):
    """Response for /insights/digest"""
    items: List[DigestItem]
    generated_at: datetime


# =============================================================================
# Startup / Shutdown Events
# =============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global reasoning_pipeline, ollama_client
    
    logger.info("starting_synapsis_backend")
    
    # Initialize Ollama client
    ollama_client = OllamaClient()
    
    # Check model availability (non-blocking)
    try:
        available = await ollama_client.ensure_models_available()
        if available:
            logger.info("ollama_models_ready", models=ollama_client.model_chain)
        else:
            logger.warning("ollama_models_not_all_available")
    except Exception as e:
        logger.error("ollama_connection_failed", error=str(e))
    
    # Initialize database
    await memory_db.initialize()
    
    # Initialize reasoning pipeline (will use mock retriever until ingestion ready)
    reasoning_pipeline = ReasoningPipeline(ollama_client=ollama_client)
    
    logger.info("synapsis_backend_ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("shutting_down_synapsis_backend")
    await memory_db.close()


# =============================================================================
# Health Endpoint
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check system health - Ollama, Qdrant, SQLite status
    """
    ollama_healthy = False
    models_available = []
    
    if ollama_client:
        try:
            # Quick health check
            models_available = await ollama_client.list_models()
            ollama_healthy = len(models_available) > 0
        except Exception:
            pass
    
    qdrant_healthy = await memory_db.check_qdrant_health()
    sqlite_healthy = await memory_db.check_sqlite_health()
    
    status = "healthy" if (ollama_healthy and sqlite_healthy) else "degraded"
    
    return HealthResponse(
        status=status,
        ollama_healthy=ollama_healthy,
        qdrant_healthy=qdrant_healthy,
        sqlite_healthy=sqlite_healthy,
        models_available=models_available,
        timestamp=datetime.now()
    )


# =============================================================================
# Query Endpoints
# =============================================================================

@app.post("/query/ask", response_model=AnswerResponse)
async def ask_question(request: AskRequest):
    """
    Ask a question and get an AI-powered answer with sources and confidence.
    
    This is the main endpoint that runs the full reasoning pipeline:
    1. Query planning (classify query type)
    2. Hybrid retrieval (dense + sparse + graph)
    3. RRF fusion (merge and rerank)
    4. LLM reasoning (synthesize answer)
    5. Critic verification (APPROVE/REVISE/REJECT)
    6. Confidence scoring
    """
    if not reasoning_pipeline:
        raise HTTPException(status_code=503, detail="Reasoning pipeline not initialized")
    
    logger.info("query_received", query=request.query[:100])
    
    start_time = asyncio.get_event_loop().time()
    
    try:
        # Run the full reasoning pipeline
        result = await reasoning_pipeline.answer(
            query=request.query,
            max_sources=request.max_sources
        )
        
        end_time = asyncio.get_event_loop().time()
        latency_ms = int((end_time - start_time) * 1000)
        
        # Convert sources to response format
        sources = [
            SourceItem(
                id=src.get("id", f"src_{i}"),
                title=src.get("title", "Untitled"),
                snippet=src.get("content", "")[:200] + "..." if len(src.get("content", "")) > 200 else src.get("content", ""),
                relevance_score=src.get("score", 0.0),
                file_path=src.get("file_path"),
                created_at=src.get("created_at")
            )
            for i, src in enumerate(result.get("sources", []))
        ]
        
        logger.info(
            "query_answered",
            query=request.query[:50],
            confidence=result.get("confidence", "NONE"),
            verification=result.get("verification", "REJECT"),
            latency_ms=latency_ms
        )
        
        return AnswerResponse(
            answer=result.get("answer", "I don't have enough information to answer this question."),
            confidence=result.get("confidence", "NONE"),
            confidence_score=result.get("confidence_score", 0.0),
            verification=result.get("verification", "REJECT"),
            sources=sources,
            reasoning_chain=result.get("reasoning_chain") if request.include_reasoning else None,
            query_type=result.get("query_type", "SIMPLE"),
            model_used=result.get("model_used", "unknown"),
            latency_ms=latency_ms
        )
        
    except Exception as e:
        logger.error("query_failed", query=request.query[:50], error=str(e))
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@app.get("/query/stream")
async def stream_answer(query: str = Query(..., min_length=1, max_length=2000)):
    """
    Stream answer tokens as Server-Sent Events (SSE).
    
    For real-time UI updates as the answer is generated.
    """
    if not reasoning_pipeline:
        raise HTTPException(status_code=503, detail="Reasoning pipeline not initialized")
    
    async def generate():
        try:
            async for chunk in reasoning_pipeline.stream_answer(query):
                yield f"data: {json.dumps(chunk)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )


# =============================================================================
# Memory Endpoints
# =============================================================================

@app.get("/memory/timeline", response_model=MemoryTimelineResponse)
async def get_memory_timeline(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    source_type: Optional[str] = None
):
    """
    Get chronological feed of ingested memories/documents.
    """
    items, total = await memory_db.get_timeline(
        page=page,
        page_size=page_size,
        source_type=source_type
    )
    
    return MemoryTimelineResponse(
        items=items,
        total_count=total,
        page=page,
        page_size=page_size
    )


@app.get("/memory/{memory_id}", response_model=MemoryItem)
async def get_memory_detail(memory_id: str):
    """
    Get full details of a single memory/document.
    """
    item = await memory_db.get_memory(memory_id)
    if not item:
        raise HTTPException(status_code=404, detail="Memory not found")
    return item


@app.get("/memory/graph", response_model=GraphResponse)
async def get_knowledge_graph(
    center_entity: Optional[str] = None,
    depth: int = Query(default=2, ge=1, le=5)
):
    """
    Get knowledge graph data for visualization.
    
    If center_entity is provided, returns a subgraph around that entity.
    Otherwise returns the most connected portion of the graph.
    """
    nodes, edges = await memory_db.get_graph(
        center_entity=center_entity,
        depth=depth
    )
    
    return GraphResponse(nodes=nodes, edges=edges)


@app.get("/memory/stats", response_model=StatsResponse)
async def get_memory_stats():
    """
    Get statistics about the knowledge base.
    """
    return await memory_db.get_stats()


# =============================================================================
# Configuration Endpoints
# =============================================================================

@app.get("/config/sources", response_model=ConfigSources)
async def get_config_sources():
    """
    Get current watched directories and exclusion patterns.
    """
    return await memory_db.get_config()


@app.put("/config/sources", response_model=ConfigSources)
async def update_config_sources(config: ConfigSources):
    """
    Update watched directories and exclusion patterns.
    
    Used by the setup wizard on first launch.
    """
    await memory_db.update_config(config)
    logger.info("config_updated", directories=config.watched_directories)
    return config


# =============================================================================
# Ingestion Status Endpoint
# =============================================================================

@app.get("/ingestion/status", response_model=IngestionStatus)
async def get_ingestion_status():
    """
    Get current ingestion pipeline status.
    """
    return await memory_db.get_ingestion_status()


# =============================================================================
# Insights Endpoint
# =============================================================================

@app.get("/insights/digest", response_model=DigestResponse)
async def get_daily_digest():
    """
    Get the latest proactive insights digest.
    
    Includes patterns detected, contradictions found, and summaries.
    """
    items = await memory_db.get_digest()
    return DigestResponse(
        items=items,
        generated_at=datetime.now()
    )


# =============================================================================
# Development / Debug Endpoints (disable in production)
# =============================================================================

@app.post("/dev/seed")
async def seed_demo_data():
    """
    Seed the database with demo data for testing.
    Only available in development mode.
    """
    from backend.seed_data import seed_sample_data
    await seed_sample_data()
    return {"status": "seeded", "message": "Demo data loaded successfully"}


@app.get("/dev/models")
async def list_models():
    """
    List available Ollama models.
    """
    if not ollama_client:
        raise HTTPException(status_code=503, detail="Ollama client not initialized")
    
    models = await ollama_client.list_models()
    return {"models": models}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host="127.0.0.1",  # Localhost only - air-gapped
        port=8000,
        reload=True,
        log_level="info"
    )
