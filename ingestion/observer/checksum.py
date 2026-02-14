"""Checksum computation and persistent store for dedup / change detection."""

import json
import hashlib
import threading
import logging
from pathlib import Path
from typing import Dict, Set, Optional

from .constants import CONFIG_DIR, CHECKSUM_DB_PATH

logger = logging.getLogger("synapsis.observer")


def compute(filepath: str, chunk_size: int = 8192) -> Optional[str]:
    """Return SHA-256 hex digest of file contents, or None on error."""
    h = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


class ChecksumStore:
    """
    Thread-safe store that maps filepath → SHA-256 checksum.

    Used to:
      - Skip unchanged files on initial scan
      - Detect real modifications (content changed, not just timestamp)
      - Detect deleted files (path no longer on disk)
    """

    def __init__(self, path: Path = CHECKSUM_DB_PATH) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._data: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def save(self) -> None:
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            logger.exception("Failed to create config directory %s for checksum store", CONFIG_DIR)
            return

        with self._lock:
            try:
                with open(self._path, "w", encoding="utf-8") as f:
                    json.dump(self._data, f)
            except OSError:
                logger.exception("Failed to save checksum store to %s", self._path)

    def get(self, filepath: str) -> Optional[str]:
        with self._lock:
            return self._data.get(filepath)

    def set(self, filepath: str, checksum: str) -> None:
        with self._lock:
            self._data[filepath] = checksum

    def remove(self, filepath: str) -> None:
        with self._lock:
            self._data.pop(filepath, None)

    def all_paths(self) -> Set[str]:
        with self._lock:
            return set(self._data.keys())
