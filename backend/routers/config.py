"""
Synapsis Backend — Config Router
GET /config/sources — get current watched directories + exclusions
PUT /config/sources — update watched directories + exclusions (setup wizard)
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
import structlog

from backend.config import settings
from backend.database import get_db, log_audit
from backend.models.schemas import (
    SourcesConfigResponse,
    SourcesConfigUpdate,
    SourceConfig,
)
from backend.utils.helpers import generate_id, utc_now

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/sources", response_model=SourcesConfigResponse)
async def get_sources():
    """Get current watched directories and exclusion configuration."""

    # Read from DB
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, path, enabled, exclude_patterns FROM sources_config ORDER BY added_at"
        ).fetchall()

    watched = []
    for row in rows:
        patterns = json.loads(row["exclude_patterns"]) if row["exclude_patterns"] else []
        watched.append(
            SourceConfig(
                id=row["id"],
                path=row["path"],
                enabled=bool(row["enabled"]),
                exclude_patterns=patterns,
            )
        )

    # Also include from settings if DB is empty
    if not watched and settings.watched_directories:
        for d in settings.watched_directories:
            watched.append(
                SourceConfig(path=d, enabled=True)
            )

    return SourcesConfigResponse(
        watched_directories=watched,
        exclude_patterns=settings.exclude_patterns,
        max_file_size_mb=settings.max_file_size_mb,
        scan_interval_seconds=settings.scan_interval_seconds,
        rate_limit_files_per_minute=settings.rate_limit_files_per_minute,
    )


@router.put("/sources", response_model=SourcesConfigResponse)
async def update_sources(config: SourcesConfigUpdate):
    """
    Update watched directories and exclusions.
    Called from the setup wizard on first run, or settings later.
    """
    with get_db() as conn:
        # Clear existing sources
        conn.execute("DELETE FROM sources_config")

        # Insert new sources
        for directory in config.watched_directories:
            conn.execute(
                """INSERT INTO sources_config (id, path, enabled, exclude_patterns, added_at)
                   VALUES (?, ?, 1, ?, ?)""",
                (
                    generate_id(),
                    directory,
                    json.dumps(config.exclude_patterns),
                    utc_now(),
                ),
            )

    # Update settings
    if config.exclude_patterns is not None:
        settings.exclude_patterns = config.exclude_patterns
    if config.max_file_size_mb is not None:
        settings.max_file_size_mb = config.max_file_size_mb
    if config.scan_interval_seconds is not None:
        settings.scan_interval_seconds = config.scan_interval_seconds
    if config.rate_limit_files_per_minute is not None:
        settings.rate_limit_files_per_minute = config.rate_limit_files_per_minute

    # Save config to disk
    _save_config_to_disk(config)

    # Restart file watcher with new directories (Person 3 pipeline)
    try:
        from backend.services.ingestion import (
            stop_file_watcher,
            start_file_watcher,
            ingestion_state,
        )

        stop_file_watcher()
        ingestion_state.watched_directories = config.watched_directories
        start_file_watcher(config.watched_directories)
    except NotImplementedError:
        logger.info("config.ingestion_not_implemented", msg="Person 3 pipeline pending")

    log_audit("config_updated", {
        "watched_directories": config.watched_directories,
        "exclude_patterns": config.exclude_patterns,
    })

    logger.info(
        "config.updated",
        directories=len(config.watched_directories),
    )

    return await get_sources()


def _save_config_to_disk(config: SourcesConfigUpdate):
    """Save configuration to JSON file for persistence."""
    config_path = Path(settings.user_config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "watched_directories": config.watched_directories,
        "exclude_patterns": config.exclude_patterns,
        "max_file_size_mb": (
            config.max_file_size_mb
            if config.max_file_size_mb is not None
            else settings.max_file_size_mb
        ),
        "scan_interval_seconds": (
            config.scan_interval_seconds
            if config.scan_interval_seconds is not None
            else settings.scan_interval_seconds
        ),
        "rate_limit_files_per_minute": (
            config.rate_limit_files_per_minute
            if config.rate_limit_files_per_minute is not None
            else settings.rate_limit_files_per_minute
        ),
    }

    config_path.write_text(json.dumps(data, indent=2))
    logger.info("config.saved_to_disk", path=str(config_path))


def load_config_from_disk() -> SourcesConfigUpdate | None:
    """Load configuration from disk if it exists."""
    config_path = Path(settings.user_config_path)
    if not config_path.exists():
        return None

    try:
        data = json.loads(config_path.read_text())
        return SourcesConfigUpdate(**data)
    except Exception as e:
        logger.warning("config.load_from_disk_failed", error=str(e))
        return None
