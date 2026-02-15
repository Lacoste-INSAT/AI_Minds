"""
Background event consumer — drains the queue with rate limiting,
retry with exponential back-off, and dead-letter logging.

Architecture spec (§ 4.5 Ingestion Queue):
  - Async queue with retry (max 3 attempts, exponential backoff)
  - Dead-letter log for failed items (don't block pipeline)
  - Idempotent: re-ingesting same file updates, doesn't duplicate
  - Background priority: low-impact on user's machine
"""

import json
import logging
import math
import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

from .checksum import ChecksumStore
from .events import FileEvent, RateLimiter, MAX_RETRIES
from .constants import CONFIG_DIR

logger = logging.getLogger("synapsis.observer")

# Dead-letter log lives alongside the checksum DB
DEAD_LETTER_PATH = CONFIG_DIR / "dead_letter.jsonl"


# ── Dead-letter helpers ──────────────────────────────────────────────────────

def _log_dead_letter(fe: FileEvent, error: str) -> None:
    """Append a failed event to the dead-letter log (JSONL)."""
    record = {
        "event_type": fe.event_type,
        "src_path": fe.src_path,
        "timestamp": fe.timestamp,
        "attempts": fe.attempts,
        "error": error,
        "dead_at": datetime.now(timezone.utc).isoformat(),
    }
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEAD_LETTER_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError:
        logger.exception("Failed to write dead-letter entry for %s", fe.src_path)

    logger.error(
        "DEAD-LETTER: %s after %d attempts — %s | error: %s",
        fe.src_path, fe.attempts, fe.event_type, error,
    )


# ── Backoff ──────────────────────────────────────────────────────────────────

def _backoff_seconds(attempt: int) -> float:
    """Exponential back-off: 2^attempt seconds (1 → 2 → 4 → …), capped at 30s."""
    return min(math.pow(2, attempt), 30.0)


# ── Processing ───────────────────────────────────────────────────────────────

# The orchestrator is imported lazily to avoid circular imports and to keep
# watchdog-only usage lightweight.
_orchestrator = None


def _get_orchestrator():
    """Lazy-load the IntakeOrchestrator singleton."""
    global _orchestrator
    if _orchestrator is None:
        from ingestion.orchestrator import IntakeOrchestrator
        _orchestrator = IntakeOrchestrator()
    return _orchestrator


def _process_event(
    fe: FileEvent,
    rate_limiter: RateLimiter,
    event_queue: "queue.Queue[FileEvent]",
) -> None:
    """
    Process a single event: rate-limit → orchestrate → retry on failure.

    On transient errors the event is re-enqueued with an incremented
    attempt counter and an exponential back-off delay.  After MAX_RETRIES
    it lands in the dead-letter log.
    """
    rate_limiter.wait()
    fe.attempts += 1

    try:
        orchestrator = _get_orchestrator()
        result = orchestrator.process(fe.event_type, fe.src_path)

        if result is not None:
            logger.info(
                "[PROCESSED] %s | %s | chunks=%s | attempt=%d",
                fe.event_type.upper(),
                fe.src_path,
                len(result) if isinstance(result, list) else "n/a",
                fe.attempts,
            )
            # TODO: hand off `result` to Memory Module (Qdrant, SQLite, Graph)

    except Exception as exc:
        fe.last_error = str(exc)

        if fe.retriable:
            delay = _backoff_seconds(fe.attempts)
            logger.warning(
                "RETRY %d/%d in %.1fs — %s | %s: %s",
                fe.attempts, MAX_RETRIES, delay,
                fe.src_path, type(exc).__name__, exc,
            )
            time.sleep(delay)
            event_queue.put(fe)
        else:
            _log_dead_letter(fe, str(exc))


def run_processor(
    event_queue: "queue.Queue[FileEvent]",
    rate_limiter: RateLimiter,
    checksum_store: ChecksumStore,
    stop_event: threading.Event,
) -> None:
    """
    Blocking loop that pops events from the queue, respects rate limits,
    routes them through the intake orchestrator, and retries on failure.
    """
    while not stop_event.is_set():
        try:
            fe = event_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        _process_event(fe, rate_limiter, event_queue)

    # Drain any remaining events after stop_event is set to avoid losing them.
    drained_count = 0
    while True:
        try:
            fe = event_queue.get_nowait()
        except queue.Empty:
            break

        drained_count += 1
        _process_event(fe, rate_limiter, event_queue)

    if drained_count:
        logger.info("Drained %d queued events on shutdown.", drained_count)

    # Persist checksums on shutdown
    checksum_store.save()
    logger.info("Event processor stopped — checksums saved.")

