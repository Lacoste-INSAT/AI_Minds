"""FileEvent DTO and a simple token-bucket rate limiter."""

import time
import threading
from datetime import datetime, timezone


class FileEvent:
    """Lightweight value object representing a filesystem change."""

    __slots__ = ("event_type", "src_path", "timestamp")

    def __init__(self, event_type: str, src_path: str) -> None:
        self.event_type = event_type        # "created" | "modified" | "deleted"
        self.src_path = src_path
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def __repr__(self) -> str:
        return f"FileEvent({self.event_type}, {self.src_path})"


class RateLimiter:
    """Token-bucket rate limiter scoped to files-per-minute."""

    def __init__(self, max_per_minute: int) -> None:
        self._interval = 60.0 / max(max_per_minute, 1)
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        """Block until the next token is available."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last
            sleep_for = self._interval - elapsed
            if sleep_for > 0:
                # Advance _last by the intended interval to avoid drift
                # from scheduler delays.
                self._last = now + sleep_for
                time.sleep(sleep_for)
            else:
                # No wait needed; consume a token at the current time.
                self._last = now
