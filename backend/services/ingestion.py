"""
Synapsis Backend — Ingestion Pipeline (Person 3)
File watching (watchdog) + parsing + chunking + embedding + entity extraction
+ storage to SQLite & Qdrant.

TODO (Person 3): Implement the full ingestion pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Ingestion state (shared across routers)
# ---------------------------------------------------------------------------

@dataclass
class IngestionState:
    """Tracks ingestion pipeline status."""
    total_files_processed: int = 0
    total_chunks_stored: int = 0
    queue_depth: int = 0
    is_scanning: bool = False
    watched_directories: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def get_status(self) -> dict[str, Any]:
        return {
            "total_files_processed": self.total_files_processed,
            "total_chunks_stored": self.total_chunks_stored,
            "queue_depth": self.queue_depth,
            "is_scanning": self.is_scanning,
            "watched_directories": self.watched_directories,
            "recent_errors": self.errors[-10:],
        }


ingestion_state = IngestionState()


# ---------------------------------------------------------------------------
# WebSocket client management
# ---------------------------------------------------------------------------

_ws_clients: list[Any] = []


def register_ws_client(ws: Any) -> None:
    _ws_clients.append(ws)


def unregister_ws_client(ws: Any) -> None:
    if ws in _ws_clients:
        _ws_clients.remove(ws)


# ---------------------------------------------------------------------------
# Stubs — Person 3 will implement
# ---------------------------------------------------------------------------


def start_file_watcher(directories: list[str]) -> None:
    """Start watchdog file observer on given directories."""
    logger.info("ingestion.watcher_stub", msg="Person 3: implement file watcher")


def stop_file_watcher() -> None:
    """Stop watchdog file observer."""
    pass


async def ingest_file(file_path: str) -> dict[str, Any] | None:
    """
    Full ingestion pipeline for a single file:
    1. Parse (route by extension)
    2. Chunk (500 chars, 100 overlap, sentence-aware)
    3. Embed (sentence-transformers)
    4. Store vectors in Qdrant
    5. Extract entities (3-layer)
    6. Build graph edges in SQLite
    7. LLM enrichment (summary, category, action_items)
    """
    raise NotImplementedError("Person 3: implement ingest_file")


async def scan_and_ingest(directories: list[str] | None = None) -> None:
    """Scan directories and ingest new/modified files."""
    raise NotImplementedError("Person 3: implement scan_and_ingest")
