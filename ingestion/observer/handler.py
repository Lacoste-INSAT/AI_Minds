"""Watchdog event handler — filters, deduplicates, and queues file events."""

import logging
import queue
from pathlib import Path
from typing import Dict, Any

from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent,
)

from .checksum import ChecksumStore, compute
from .filters import is_supported, passes_all
from .events import FileEvent

logger = logging.getLogger("synapsis.observer")


class IngestionHandler(FileSystemEventHandler):
    """
    Watchdog callback handler.

    Flow: raw OS event → filter → checksum dedup → enqueue.
    """

    def __init__(
        self,
        config: Dict[str, Any],
        checksum_store: ChecksumStore,
        event_queue: "queue.Queue[FileEvent]",
    ) -> None:
        super().__init__()
        self._config = config
        self._checksums = checksum_store
        self._queue = event_queue

    # ── Watchdog callbacks ──────────────────────────────────────────────────

    def on_created(self, event: FileCreatedEvent) -> None:
        if not event.is_directory:
            self._handle("created", event.src_path)

    def on_modified(self, event: FileModifiedEvent) -> None:
        if not event.is_directory:
            self._handle("modified", event.src_path)

    def on_deleted(self, event: FileDeletedEvent) -> None:
        if not event.is_directory:
            self._handle("deleted", event.src_path)

    def on_moved(self, event: FileMovedEvent) -> None:
        if not event.is_directory:
            src_path = str(Path(event.src_path).absolute())
            dest_path = str(Path(event.dest_path).absolute())

            # Transfer checksum from old path to avoid reprocessing identical content
            old_checksum = self._checksums.get(src_path)
            self._handle("deleted", event.src_path)
            if old_checksum is not None:
                self._checksums.set(dest_path, old_checksum)
            self._handle("created", event.dest_path)

    # ── Internal logic ──────────────────────────────────────────────────────

    def _handle(self, event_type: str, filepath: str) -> None:
        # Use absolute() instead of resolve() to avoid following symlinks
        # outside watched directory trees.
        filepath = str(Path(filepath).absolute())

        # Deletes: only queue for tracked files that pass filters
        # so the knowledge graph stays in sync
        if event_type == "deleted":
            # Apply the same filters (extension, exclusions, etc.) used for other events
            if not passes_all(filepath, self._config):
                return

            # Only queue a delete if we have previously tracked this file
            old_checksum = self._checksums.get(filepath)
            if old_checksum is None:
                logger.debug("Skipping delete for untracked file: %s", filepath)
                return

            self._checksums.remove(filepath)
            self._enqueue(event_type, filepath)
            return

        # Filter: extension + exclusion + size
        if not passes_all(filepath, self._config):
            return

        # Dedup: only queue if content actually changed
        new_checksum = compute(filepath)
        if new_checksum is None:
            return

        old_checksum = self._checksums.get(filepath)
        if old_checksum == new_checksum:
            logger.debug("Unchanged (checksum match), skipping: %s", filepath)
            return

        self._checksums.set(filepath, new_checksum)
        self._enqueue("created" if old_checksum is None else "modified", filepath)

    def _enqueue(self, event_type: str, filepath: str) -> None:
        fe = FileEvent(event_type, filepath)
        self._queue.put(fe)
        logger.info("Queued %s", fe)
