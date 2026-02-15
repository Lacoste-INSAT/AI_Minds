"""
Runtime incident service.
Persists incidents, keeps in-memory cache, and broadcasts to subscribers.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import structlog

from backend.config import settings
from backend.database import get_db, log_audit
from backend.models.schemas import RuntimeIncident
from backend.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

_cache: list[RuntimeIncident] = []
_subscribers: list[Callable[[RuntimeIncident], Awaitable[None]]] = []
_cache_loaded = False


def subscribe(handler: Callable[[RuntimeIncident], Awaitable[None]]) -> None:
    if handler not in _subscribers:
        _subscribers.append(handler)


def unsubscribe(handler: Callable[[RuntimeIncident], Awaitable[None]]) -> None:
    if handler in _subscribers:
        _subscribers.remove(handler)


def _load_cache_once() -> None:
    global _cache_loaded
    if _cache_loaded:
        return
    with get_db() as conn:
        rows = conn.execute(
            """SELECT id, timestamp, subsystem, operation, reason, severity, blocked, payload
               FROM runtime_incidents
               ORDER BY timestamp DESC
               LIMIT ?""",
            (settings.incident_retention_limit,),
        ).fetchall()
    _cache.extend(
        RuntimeIncident(
            id=row["id"],
            timestamp=row["timestamp"],
            subsystem=row["subsystem"],
            operation=row["operation"],
            reason=row["reason"],
            severity=row["severity"],
            blocked=bool(row["blocked"]),
            payload=json.loads(row["payload"]) if row["payload"] else None,
        )
        for row in reversed(rows)
    )
    _cache_loaded = True


def list_incidents(limit: int = 50) -> list[RuntimeIncident]:
    _load_cache_once()
    if limit <= 0:
        return []
    return _cache[-limit:]


async def emit_incident(
    subsystem: str,
    operation: str,
    reason: str,
    *,
    severity: str = "warning",
    blocked: bool = False,
    payload: dict[str, Any] | None = None,
) -> RuntimeIncident:
    _load_cache_once()

    incident = RuntimeIncident(
        id=generate_id(),
        timestamp=utc_now(),
        subsystem=subsystem,
        operation=operation,
        reason=reason,
        severity=severity,
        blocked=blocked,
        payload=payload,
    )

    with get_db() as conn:
        conn.execute(
            """INSERT INTO runtime_incidents
               (id, timestamp, subsystem, operation, reason, severity, blocked, payload)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                incident.id,
                incident.timestamp,
                incident.subsystem,
                incident.operation,
                incident.reason,
                incident.severity,
                1 if incident.blocked else 0,
                json.dumps(incident.payload) if incident.payload else None,
            ),
        )
        log_audit("runtime_incident", incident.model_dump(), conn=conn)

    _cache.append(incident)
    if len(_cache) > settings.incident_retention_limit:
        del _cache[:-settings.incident_retention_limit]

    logger.warning(
        "runtime.incident",
        subsystem=subsystem,
        operation=operation,
        severity=severity,
        blocked=blocked,
        reason=reason,
    )

    if _subscribers:
        await asyncio.gather(
            *[handler(incident) for handler in list(_subscribers)],
            return_exceptions=True,
        )

    return incident

