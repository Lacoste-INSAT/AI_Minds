"""
Synapsis Security — Input Sanitiser
====================================

General-purpose input sanitisation applied before any processing:
  - Length limits
  - Control-character stripping
  - HTML/script tag removal
  - Path-traversal prevention
  - Null-byte injection prevention

Usage::

    from backend.security.sanitiser import sanitise

    clean = sanitise(user_input, max_length=4096)
"""

from __future__ import annotations

import re

import structlog

logger = structlog.get_logger(__name__)


class InputSanitiser:
    """Configurable input sanitiser."""

    def __init__(
        self,
        max_length: int = 10_000,
        strip_html: bool = True,
        strip_control: bool = True,
        strip_null_bytes: bool = True,
        strip_path_traversal: bool = True,
    ) -> None:
        self.max_length = max_length
        self.strip_html = strip_html
        self.strip_control = strip_control
        self.strip_null_bytes = strip_null_bytes
        self.strip_path_traversal = strip_path_traversal

    def clean(self, text: str) -> str:
        """Apply all configured sanitisation passes."""
        if not text:
            return ""

        result = text

        # 1. Null-byte injection
        if self.strip_null_bytes:
            result = result.replace("\x00", "")

        # 2. Control characters (keep \n, \r, \t)
        if self.strip_control:
            result = re.sub(r"[\x01-\x08\x0b\x0c\x0e-\x1f\x7f]", "", result)

        # 3. HTML / script tags
        if self.strip_html:
            result = re.sub(r"<script[^>]*>.*?</script>", "", result,
                            flags=re.IGNORECASE | re.DOTALL)
            result = re.sub(r"<style[^>]*>.*?</style>", "", result,
                            flags=re.IGNORECASE | re.DOTALL)
            result = re.sub(r"<!--.*?-->", "", result, flags=re.DOTALL)
            # Remove event handlers
            result = re.sub(r"\bon\w+\s*=\s*[\"'][^\"']*[\"']", "", result,
                            flags=re.IGNORECASE)

        # 4. Path traversal sequences
        if self.strip_path_traversal:
            result = result.replace("../", "")
            result = result.replace("..\\", "")
            result = result.replace("%2e%2e%2f", "")
            result = result.replace("%2e%2e/", "")

        # 5. Length limit
        if len(result) > self.max_length:
            result = result[: self.max_length]
            logger.debug("sanitiser.truncated", original=len(text), max=self.max_length)

        return result.strip()

    def clean_filename(self, filename: str) -> str:
        """Sanitise a filename to prevent path traversal and injection."""
        # Remove directory components
        name = filename.replace("\\", "/").split("/")[-1]
        # Remove null bytes
        name = name.replace("\x00", "")
        # Remove path traversal
        name = name.replace("..", "")
        # Remove special shell characters
        name = re.sub(r"[;&|`$]", "", name)
        # Only allow safe characters
        name = re.sub(r"[^\w.\-\s]", "_", name)
        return name.strip() or "unnamed"

    def clean_path(self, path: str) -> str:
        """Sanitise a filesystem path."""
        clean = path.replace("\x00", "")
        # Normalise separators
        clean = clean.replace("\\", "/")
        # Remove path traversal
        while "../" in clean:
            clean = clean.replace("../", "")
        # Remove double slashes
        clean = re.sub(r"/{2,}", "/", clean)
        return clean


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_sanitiser = InputSanitiser()


def sanitise(text: str, max_length: int | None = None) -> str:
    """Quick sanitise with default settings."""
    if max_length is not None:
        return InputSanitiser(max_length=max_length).clean(text)
    return _default_sanitiser.clean(text)


def sanitise_filename(filename: str) -> str:
    """Quick filename sanitise."""
    return _default_sanitiser.clean_filename(filename)
