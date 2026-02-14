"""SynapsisWatcher — main controller that orchestrates all observer components."""

import time
import logging
import threading
from collections import deque
from typing import Dict, Optional, Deque, Any

from watchdog.observers import Observer

from .config import load_config, save_config, resolve_directories
from .constants import CONFIG_PATH, DEFAULT_CONFIG
from .checksum import ChecksumStore
from .events import FileEvent, RateLimiter
from .handler import IngestionHandler
from .scanner import initial_scan
from .processor import run_processor

logger = logging.getLogger("synapsis.observer")


class SynapsisWatcher:
    """
    High-level controller that ties together:
      - config loading
      - initial directory scan
      - live watchdog monitoring
      - rate-limited event processing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._config = config or load_config()
        self._checksums = ChecksumStore()
        self._queue: Deque[FileEvent] = deque()
        self._rate_limiter = RateLimiter(
            self._config.get("rate_limit_files_per_minute", 10)
        )
        self._observer = Observer()
        self._stop = threading.Event()
        self._processor_thread: Optional[threading.Thread] = None
        self._scan_thread: Optional[threading.Thread] = None

    @property
    def queue(self) -> Deque[FileEvent]:
        return self._queue

    def start(self) -> None:
        """Start live watch immediately, then scan in the background."""
        directories = resolve_directories(
            self._config.get("watched_directories", [])
        )
        if not directories:
            logger.error("No valid directories to watch — exiting.")
            return

        logger.info(
            "Watching %d director(ies): %s",
            len(directories),
            [str(d) for d in directories],
        )

        # 1 — Start live filesystem watcher FIRST (instant responsiveness)
        handler = IngestionHandler(self._config, self._checksums, self._queue)
        for d in directories:
            self._observer.schedule(handler, str(d), recursive=True)
        self._observer.start()
        logger.info("Live filesystem watcher started.")

        # 2 — Background event processor thread
        self._processor_thread = threading.Thread(
            target=run_processor,
            args=(self._queue, self._rate_limiter, self._checksums, self._stop),
            daemon=True,
        )
        self._processor_thread.start()

        # 3 — Initial scan in background (catches offline changes without blocking)
        self._scan_thread = threading.Thread(
            target=self._background_scan,
            args=(directories,),
            daemon=True,
        )
        self._scan_thread.start()

    def _background_scan(self, directories):
        """Run initial scan in background to catch offline changes."""
        logger.info("Background scan starting (%d directories)...", len(directories))
        try:
            count = initial_scan(
                directories, self._config, self._checksums, self._queue
            )
            logger.info("Background scan complete — %d events queued.", count)
        except Exception as exc:
            logger.error("Background scan failed: %s", exc)

    def stop(self) -> None:
        """Gracefully shut down watcher + processor."""
        logger.info("Stopping Synapsis watcher\u2026")
        self._stop.set()
        self._observer.stop()
        self._observer.join()
        if self._scan_thread:
            self._scan_thread.join(timeout=10)
        if self._processor_thread:
            self._processor_thread.join(timeout=5)
        self._checksums.save()
        logger.info("Synapsis watcher stopped.")


def main() -> None:
    """CLI entry point."""
    from . import _setup_logging
    _setup_logging()

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        logger.info("Created default config at %s", CONFIG_PATH)

    watcher = SynapsisWatcher()
    watcher.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        watcher.stop()


if __name__ == "__main__":
    main()
