"""Background event consumer — drains the queue with rate limiting."""

import logging
import queue
import threading

from .checksum import ChecksumStore
from .events import FileEvent, RateLimiter

logger = logging.getLogger("synapsis.observer")


def _process_event(fe: FileEvent, rate_limiter: RateLimiter) -> None:
    """Process a single event with rate limiting."""
    rate_limiter.wait()
    # TODO: hand off to intake orchestrator / parser router
    logger.info(
        "[PROCESS] %s | %s | %s",
        fe.event_type.upper(),
        fe.src_path,
        fe.timestamp,
    )


def run_processor(
    event_queue: "queue.Queue[FileEvent]",
    rate_limiter: RateLimiter,
    checksum_store: ChecksumStore,
    stop_event: threading.Event,
) -> None:
    """
    Blocking loop that pops events from the queue, respects rate limits,
    and logs them.  Downstream processing (parsing, embedding, etc.)
    will plug in here.
    """
    while not stop_event.is_set():
        try:
            fe = event_queue.get(timeout=0.25)
        except queue.Empty:
            continue

        _process_event(fe, rate_limiter)

    # Drain any remaining events after stop_event is set to avoid losing them.
    drained_count = 0
    while True:
        try:
            fe = event_queue.get_nowait()
        except queue.Empty:
            break

        drained_count += 1
        _process_event(fe, rate_limiter)

    if drained_count:
        logger.info("Drained %d queued events on shutdown.", drained_count)

    # Persist checksums on shutdown
    checksum_store.save()
    logger.info("Event processor stopped — checksums saved.")
