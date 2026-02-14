"""
Synapsis Backend — Utility helpers
"""

import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path


def generate_id() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


def utc_now() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


def file_checksum(filepath: str | Path, algorithm: str = "sha256") -> str:
    """Compute hex digest checksum for a file."""
    h = hashlib.new(algorithm)
    path = Path(filepath)
    with path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def text_checksum(text: str) -> str:
    """Compute sha256 of text content."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_modality(filepath: str | Path) -> str:
    """Determine modality from file extension."""
    ext = Path(filepath).suffix.lower()
    modality_map = {
        ".txt": "text",
        ".md": "text",
        ".pdf": "pdf",
        ".jpg": "image",
        ".jpeg": "image",
        ".png": "image",
        ".bmp": "image",
        ".tiff": "image",
        ".wav": "audio",
        ".mp3": "audio",
        ".m4a": "audio",
        ".flac": "audio",
        ".ogg": "audio",
        ".json": "json",
        ".docx": "text",
    }
    return modality_map.get(ext, "text")


SUPPORTED_EXTENSIONS = {
    ".txt", ".md", ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".tiff",
    ".wav", ".mp3", ".m4a", ".flac", ".ogg", ".json", ".docx",
}


def is_supported_file(filepath: str | Path) -> bool:
    """Check if a file has a supported extension."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS


def file_size_mb(filepath: str | Path) -> float:
    """Get file size in megabytes."""
    return Path(filepath).stat().st_size / (1024 * 1024)
