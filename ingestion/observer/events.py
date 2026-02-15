"""FileEvent DTO and a simple token-bucket rate limiter."""

import time
import threading
from datetime import datetime, timezone

# Max attempts before an event is sent to the dead-letter log.
MAX_RETRIES = 3


class FileEvent:
    """Lightweight value object representing a filesystem change."""

    __slots__ = ("event_type", "src_path", "timestamp", "attempts", "last_error")

    def __init__(self, event_type: str, src_path: str) -> None:
        self.event_type = event_type        # "created" | "modified" | "deleted"
        self.src_path = src_path
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.attempts: int = 0
        self.last_error: str = ""

    @property
    def retriable(self) -> bool:
        """True if this event has not exhausted its retry budget."""
        return self.attempts < MAX_RETRIES

    def __repr__(self) -> str:
        retry_info = f", attempt={self.attempts}" if self.attempts else ""
        return f"FileEvent({self.event_type}, {self.src_path}{retry_info})"


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
