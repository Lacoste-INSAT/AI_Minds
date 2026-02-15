"""Shared constants for the observer package."""

import os
from pathlib import Path
from typing import Set, Dict, List, Any


# Extensions the ingestion pipeline can process
SUPPORTED_EXTENSIONS: Set[str] = {
    ".pdf",     # PyMuPDF
    ".txt",     # plain text
    ".md",      # markdown
    ".docx",    # Word documents
    ".jpg",     # pytesseract OCR
    ".jpeg",
    ".png",
    ".wav",     # faster-whisper
    ".mp3",
    ".json",    # structured notes
}


def _is_docker() -> bool:
    """Detect if running inside a Docker container."""
    return (
        os.path.exists("/.dockerenv")
        or os.environ.get("SYNAPSIS_DOCKER") == "1"
        or os.environ.get("container") is not None
    )


# Docker-aware default watched directories
_DOCKER_WATCHED_DIRS: List[str] = [
    "/app/watched",
]

_HOST_WATCHED_DIRS: List[str] = [
    "~/Documents",
    "~/Desktop",
    "~/Downloads",
    "~/Pictures",
    "~/Music",
]

# Default user config (created on first run by the setup wizard)
DEFAULT_CONFIG: Dict[str, Any] = {
    "watched_directories": _DOCKER_WATCHED_DIRS if _is_docker() else _HOST_WATCHED_DIRS,
    "exclude_patterns": [
        "node_modules/**",
        ".git/**",
        "__pycache__/**",
        "*.exe",
        "*.dll",
        "*.tmp",
        "~$*",
    ],
    "max_file_size_mb": 50,
    "rate_limit_files_per_minute": 10,
}

# Paths
CONFIG_DIR = Path.home() / ".synapsis"
CONFIG_PATH = CONFIG_DIR / "config.json"
CHECKSUM_DB_PATH = CONFIG_DIR / "checksums.json"
