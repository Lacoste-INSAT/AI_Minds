"""
Synapsis Backend — Health Check Service
Checks: Ollama, Qdrant, SQLite, disk space.
"""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import structlog

from backend.config import settings
from backend.models.schemas import HealthResponse, ServiceStatus

logger = structlog.get_logger(__name__)

_start_time = time.time()


async def check_health() -> HealthResponse:
    """Run all health checks and return aggregated status."""

    ollama_status = await _check_ollama()
    qdrant_status = _check_qdrant()
    sqlite_status = _check_sqlite()
    disk_free_gb = _check_disk()

    # Determine overall status
    statuses = [ollama_status.status, qdrant_status.status, sqlite_status.status]
    if all(s == "up" for s in statuses):
        overall = "healthy"
    elif sqlite_status.status == "up":
        overall = "degraded"
    else:
        overall = "unhealthy"

    uptime = time.time() - _start_time

    return HealthResponse(
        status=overall,
        ollama=ollama_status,
        qdrant=qdrant_status,
        sqlite=sqlite_status,
        disk_free_gb=disk_free_gb,
        uptime_seconds=round(uptime, 1),
    )


async def _check_ollama() -> ServiceStatus:
    """Check Ollama connectivity and model availability."""
    try:
        from backend.services.ollama_client import ollama_client
        from backend.services.model_router import get_lane_status

        available = await ollama_client.is_available()
        if not available:
            return ServiceStatus(status="down", detail={"error": "Ollama not reachable"})

        model_info = await ollama_client.get_model_info()
        lanes = await get_lane_status()
        return ServiceStatus(
            status="up",
            detail={
                "model": model_info.get("model"),
                "tier": model_info.get("tier"),
                "lanes": lanes,
            },
        )
    except Exception as e:
        return ServiceStatus(status="down", detail={"error": str(e)})


def _check_qdrant() -> ServiceStatus:
    """Check Qdrant connectivity."""
    try:
        from backend.services.qdrant_service import get_collection_info

        info = get_collection_info()
        return ServiceStatus(
            status=info.get("status", "down"),
            detail={
                "vectors_count": info.get("vectors_count", 0),
                "points_count": info.get("points_count", 0),
            },
        )
    except Exception as e:
        return ServiceStatus(status="down", detail={"error": str(e)})


def _check_sqlite() -> ServiceStatus:
    """Check SQLite database."""
    try:
        from backend.database import get_db

        with get_db() as conn:
            # Quick read test
            nodes_count = conn.execute("SELECT COUNT(*) as c FROM nodes").fetchone()["c"]
            edges_count = conn.execute("SELECT COUNT(*) as c FROM edges").fetchone()["c"]
            docs_count = conn.execute("SELECT COUNT(*) as c FROM documents").fetchone()["c"]

        return ServiceStatus(
            status="up",
            detail={
                "nodes_count": nodes_count,
                "edges_count": edges_count,
                "documents_count": docs_count,
            },
        )
    except Exception as e:
        return ServiceStatus(status="down", detail={"error": str(e)})


def _check_disk() -> float | None:
    """Check available disk space."""
    try:
        db_path = Path(settings.sqlite_path).parent
        usage = shutil.disk_usage(str(db_path))
        return round(usage.free / (1024**3), 1)
    except Exception:
        return None
