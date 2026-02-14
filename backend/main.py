"""
Synapsis Backend — FastAPI Application
Main entry point. Binds to 127.0.0.1:8000 (localhost only, air-gapped).
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from backend.config import settings
from backend.database import init_db
from backend.utils.logging import setup_logging

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

setup_logging(debug=settings.debug)
logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown handlers."""
    logger.info("app.starting", version=settings.app_version)

    # --- STARTUP ---

    # 1. Initialize SQLite database
    init_db()

    # 2. Ensure Qdrant collection exists
    try:
        from backend.services.qdrant_service import ensure_collection
        ensure_collection()
    except Exception as e:
        logger.warning("startup.qdrant_init_failed", error=str(e))

    # 3. Check Ollama availability and select model
    try:
        from backend.services.ollama_client import ollama_client
        model = await ollama_client.get_available_model()
        if model:
            logger.info("startup.ollama_ready", model=model)
        else:
            logger.warning("startup.ollama_no_model", msg="No Ollama model found — LLM features disabled")
    except Exception as e:
        logger.warning("startup.ollama_check_failed", error=str(e))

    # 4. Load saved config and start file watcher
    try:
        from backend.routers.config import load_config_from_disk
        from backend.services.ingestion import start_file_watcher, ingestion_state

        saved_config = load_config_from_disk()
        if saved_config and saved_config.watched_directories:
            ingestion_state.watched_directories = saved_config.watched_directories
            start_file_watcher(saved_config.watched_directories)
            logger.info("startup.watcher_started", directories=len(saved_config.watched_directories))
    except Exception as e:
        logger.warning("startup.watcher_failed", error=str(e))

    # 5. Build initial BM25 index
    try:
        from backend.services.retrieval import build_bm25_index
        build_bm25_index()
    except Exception as e:
        logger.warning("startup.bm25_init_failed", error=str(e))

    # 6. Load graph into memory
    try:
        from backend.services.graph_service import get_graph
        G = get_graph()
        logger.info("startup.graph_loaded", nodes=G.number_of_nodes(), edges=G.number_of_edges())
    except Exception as e:
        logger.warning("startup.graph_load_failed", error=str(e))

    # 7. Start APScheduler for proactive engine
    _start_scheduler()

    logger.info("app.started", host=settings.host, port=settings.port)

    yield  # ← App is running

    # --- SHUTDOWN ---
    logger.info("app.shutting_down")

    # Stop file watcher
    try:
        from backend.services.ingestion import stop_file_watcher
        stop_file_watcher()
    except Exception:
        pass

    # Close Ollama client
    try:
        from backend.services.ollama_client import ollama_client
        await ollama_client.close()
    except Exception:
        pass

    # Stop scheduler
    _stop_scheduler()

    logger.info("app.stopped")


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

_scheduler = None


def _start_scheduler():
    """Start APScheduler for periodic proactive tasks."""
    global _scheduler
    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from backend.services.proactive import generate_digest, detect_patterns

        _scheduler = AsyncIOScheduler()
        _scheduler.add_job(generate_digest, "interval", hours=6, id="digest")
        _scheduler.add_job(detect_patterns, "interval", hours=6, id="patterns")
        _scheduler.start()
        logger.info("scheduler.started")
    except ImportError:
        logger.warning("scheduler.apscheduler_not_installed")
    except Exception as e:
        logger.warning("scheduler.start_failed", error=str(e))


def _stop_scheduler():
    global _scheduler
    if _scheduler:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Synapsis API",
    description=(
        "Personal Knowledge Assistant — Zero-touch ingestion, air-gapped, "
        "local-only. Hybrid retrieval (dense + sparse + graph), "
        "LLM reasoning with critic verification."
    ),
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Register Routers
# ---------------------------------------------------------------------------

from backend.routers.query import router as query_router
from backend.routers.memory import router as memory_router
from backend.routers.config import router as config_router
from backend.routers.ingestion import router as ingestion_router
from backend.routers.health import router as health_router
from backend.routers.insights import router as insights_router

app.include_router(query_router)
app.include_router(memory_router)
app.include_router(config_router)
app.include_router(ingestion_router)
app.include_router(health_router)
app.include_router(insights_router)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Root endpoint — API info."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs",
    }
