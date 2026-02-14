"""Initial directory scan — catches anything added/changed while offline."""

import os
import logging
import queue
from pathlib import Path
from typing import Dict, List, Set, Any

from .checksum import ChecksumStore, compute
from .filters import passes_all
from .events import FileEvent

logger = logging.getLogger("synapsis.observer")


def initial_scan(
    directories: List[Path],
    config: Dict[str, Any],
    checksum_store: ChecksumStore,
    event_queue: "queue.Queue[FileEvent]",
) -> int:
    """
    Walk all watched directories.  Queue files that are new or modified
    since the last run.  Detect deletions of previously-known files.

    On the very first run (empty checksum DB), silently indexes all existing
    files without queuing events — builds a baseline so only future changes
    are reported.

    Returns the number of events queued.
    """
    queued = 0
    indexed = 0
    known_paths = checksum_store.all_paths()
    first_run = len(known_paths) == 0
    found_paths: Set[str] = set()

    if first_run:
        logger.info("First run — indexing existing files (no events queued).")

    for directory in directories:
        for root, _dirs, files in os.walk(directory):
            for name in files:
                filepath = str(Path(root, name).absolute())
                found_paths.add(filepath)

                if not passes_all(filepath, config):
                    continue

                new_checksum = compute(filepath)
                if new_checksum is None:
                    continue

                old_checksum = checksum_store.get(filepath)
                if old_checksum == new_checksum:
                    indexed += 1
                    continue

                checksum_store.set(filepath, new_checksum)
                indexed += 1

                # First run: just index, don't queue
                if first_run:
                    continue

                event_type = "created" if old_checksum is None else "modified"
                event_queue.put(FileEvent(event_type, filepath))
                queued += 1

    # Files we tracked before but no longer exist → deleted (skip on first run)
    # Apply the same filter set used for creates/modifies so config changes
    # don't generate spurious deletions for newly-excluded files.
    if not first_run:
        for missing in known_paths - found_paths:
            if passes_all(missing, config):
                checksum_store.remove(missing)
                event_queue.put(FileEvent("deleted", missing))
                queued += 1

    if first_run:
        checksum_store.save()
        logger.info("Baseline indexed — %d files cataloged.", indexed)
    else:
        logger.info("Initial scan complete — %d event(s) queued.", queued)
    return queued
