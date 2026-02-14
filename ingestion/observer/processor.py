"""Background event consumer — drains the queue with rate limiting."""

import time
import logging
import threading
from collections import deque

from .checksum import ChecksumStore
from .events import FileEvent, RateLimiter

logger = logging.getLogger("synapsis.observer")


def run_processor(
    event_queue: deque,
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
            fe = event_queue.popleft()
        except IndexError:
            # Queue empty — brief sleep to avoid busy-waiting
            time.sleep(0.25)
            continue

        rate_limiter.wait()

        # TODO: hand off to intake orchestrator / parser router
        logger.info(
            "[PROCESS] %s | %s | %s",
            fe.event_type.upper(),
            fe.src_path,
            fe.timestamp,
        )

    # Persist checksums on shutdown
    checksum_store.save()
    logger.info("Event processor stopped — checksums saved.")
