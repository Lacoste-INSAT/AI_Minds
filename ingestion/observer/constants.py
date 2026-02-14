"""Shared constants for the observer package."""

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

# Default user config (created on first run by the setup wizard)
DEFAULT_CONFIG: Dict[str, Any] = {
    "watched_directories": [
        "~/Documents",
        "~/Desktop",
        "~/Downloads",
        "~/Pictures",
        "~/Music",
    ],
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
    "scan_interval_seconds": 30,
    "rate_limit_files_per_minute": 10,
}

# Paths
CONFIG_DIR = Path.home() / ".synapsis"
CONFIG_PATH = CONFIG_DIR / "config.json"
CHECKSUM_DB_PATH = CONFIG_DIR / "checksums.json"
