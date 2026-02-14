"""
Synapsis Backend — Health Router
GET /health — Ollama, Qdrant, SQLite status
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.models.schemas import HealthResponse
from backend.services.health import check_health

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Service health check.
    Returns status of Ollama, Qdrant, SQLite, and disk space.
    """
    return await check_health()
