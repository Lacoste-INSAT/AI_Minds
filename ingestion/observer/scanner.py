"""Initial directory scan — catches anything added/changed while offline."""

import os
import logging
from pathlib import Path
from collections import deque
from typing import Dict, List, Set, Any

from .checksum import ChecksumStore, compute
from .filters import is_supported, passes_all
from .events import FileEvent

logger = logging.getLogger("synapsis.observer")


def initial_scan(
    directories: List[Path],
    config: Dict[str, Any],
    checksum_store: ChecksumStore,
    event_queue: deque,
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
    known_paths = checksum_store.all_paths()
    first_run = len(known_paths) == 0
    found_paths: Set[str] = set()

    if first_run:
        logger.info("First run — indexing existing files (no events queued).")

    for directory in directories:
        for root, _dirs, files in os.walk(directory):
            for name in files:
                filepath = str(Path(root, name).resolve())
                found_paths.add(filepath)

                if not passes_all(filepath, config):
                    continue

                new_checksum = compute(filepath)
                if new_checksum is None:
                    continue

                old_checksum = checksum_store.get(filepath)
                if old_checksum == new_checksum:
                    continue

                checksum_store.set(filepath, new_checksum)

                # First run: just index, don't queue
                if first_run:
                    continue

                event_type = "created" if old_checksum is None else "modified"
                event_queue.append(FileEvent(event_type, filepath))
                queued += 1

    # Files we tracked before but no longer exist → deleted (skip on first run)
    if not first_run:
        for missing in known_paths - found_paths:
            if is_supported(missing):
                checksum_store.remove(missing)
                event_queue.append(FileEvent("deleted", missing))
                queued += 1

    if first_run:
        checksum_store.save()
        logger.info("Baseline indexed — %d files cataloged.", len(found_paths))
    else:
        logger.info("Initial scan complete — %d event(s) queued.", queued)
    return queued
