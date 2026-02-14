"""
FastAPI application for the Multi-Modal Retrieval Service.
Handles data pool analysis and graph generation for biomedical research objectives.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import sys
from datetime import datetime

import dotenv
dotenv.load_dotenv()


# Import routers
from api.retrieval_router import router as retrieval_router
from api.protein_graph_router import router as protein_graph_router
from api.expand_router import router as expand_router

# Configure logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retrieval_service.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Multi-Modal Retrieval Service")
    
    # Startup
    try:
        # Initialize any required resources here
        logger.info("Service initialization completed")
        yield
    finally:
        # Cleanup
        logger.info("Shutting down Multi-Modal Retrieval Service")

# Create FastAPI application
app = FastAPI(
    title="Multi-Modal Retrieval Service",
    description="""
    Advanced AI-powered service for processing multi-modal data pools and generating 
    knowledge graphs for biomedical research objectives.
    
    Features:
    - Multi-modal file parsing (PDF, CIF, PDB, text, images)
    - AI-powered content analysis and relationship detection
    - Iterative retrieval based on research objectives
    - Knowledge graph generation with linked data entries
    - Specialized sub-LLM tools for domain-specific analysis
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(retrieval_router)
app.include_router(protein_graph_router)
app.include_router(expand_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Multi-Modal Retrieval Service",
        "version": "1.0.0",
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "docs": "/docs",
            "health": "/api/v1/retrieval/health",
            "analyze": "/api/v1/retrieval/analyze",
            "analyze_async": "/api/v1/retrieval/analyze-async"
        },
        "features": [
            "Multi-modal data processing",
            "AI-powered graph generation",
            "Iterative retrieval",
            "Relationship detection",
            "Objective-based analysis"
        ]
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception on {request.url}: {str(exc)}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests."""
    start_time = datetime.now()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    # Process request
    response = await call_next(request)
    
    # Log response
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"Response: {response.status_code} ({process_time:.3f}s)")
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )