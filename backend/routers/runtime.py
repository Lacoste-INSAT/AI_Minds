"""
Runtime Router
Exposes runtime policy and incident feed.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from backend.config import settings
from backend.models.schemas import RuntimeIncident, RuntimePolicyResponse
from backend.services.runtime_incidents import list_incidents

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/policy", response_model=RuntimePolicyResponse)
async def get_runtime_policy():
    return RuntimePolicyResponse(
        fail_fast=settings.runtime_fail_fast,
        allow_model_fallback=settings.allow_model_fallback,
        lane_assignment={
            "interactive_heavy": "gpu",
            "background_enrichment": "cpu",
            "background_proactive": "cpu",
            "classification_light": "cpu",
        },
        outage_policy="partial_service_with_incident",
    )


@router.get("/incidents", response_model=list[RuntimeIncident])
async def get_runtime_incidents(limit: int = Query(50, ge=1, le=500)):
    return list_incidents(limit=limit)

