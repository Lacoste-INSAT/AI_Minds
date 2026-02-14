"""
Synapsis Backend — Insights Router
GET /insights/digest — latest proactive digest
GET /insights/connections — recent connection discoveries
GET /insights/all — all recent insights
"""

from __future__ import annotations

from fastapi import APIRouter
import structlog

from backend.models.schemas import DigestResponse, InsightItem
from backend.services.proactive import (
    generate_digest,
    detect_patterns,
    get_recent_insights,
)
from backend.utils.helpers import utc_now

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/digest", response_model=DigestResponse)
async def get_digest():
    """Generate and return the latest knowledge digest."""
    digest = await generate_digest()

    return DigestResponse(
        insights=[
            InsightItem(
                type="digest",
                title="Knowledge Digest",
                description=digest.get("summary", ""),
                related_entities=[
                    e["name"] for e in digest.get("recent_entities", [])
                ],
                created_at=digest.get("generated_at", utc_now()),
            )
        ],
        generated_at=digest.get("generated_at"),
    )


@router.get("/patterns")
async def get_patterns():
    """Detect and return knowledge graph patterns."""
    patterns = await detect_patterns()
    return {"patterns": patterns}


@router.get("/all", response_model=DigestResponse)
async def get_all_insights():
    """Return all recent insights."""
    insights = get_recent_insights(limit=50)
    return DigestResponse(
        insights=[InsightItem(**i) for i in insights],
        generated_at=utc_now(),
    )
