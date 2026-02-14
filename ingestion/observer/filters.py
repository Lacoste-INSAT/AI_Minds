"""File filtering — extension, exclusion patterns, and size limit checks."""

import os
import fnmatch
from pathlib import Path
from typing import Dict, List, Any

from .constants import SUPPORTED_EXTENSIONS


def is_supported(filepath: str) -> bool:
    """True if the file has a supported extension."""
    return Path(filepath).suffix.lower() in SUPPORTED_EXTENSIONS


def is_excluded(filepath: str, exclude_patterns: List[str]) -> bool:
    """True if the path matches any exclusion glob."""
    fp = filepath.replace("\\", "/")
    for pattern in exclude_patterns:
        if fnmatch.fnmatch(fp, f"*/{pattern}") or fnmatch.fnmatch(fp, pattern):
            return True
        # Directory-level globs like "node_modules/**" or "src/node_modules/**"
        if "/**" in pattern:
            base = pattern.split("/**", 1)[0].strip("/")
            if base:
                fp_parts = Path(fp).parts
                base_parts = Path(base).parts
                if len(base_parts) <= len(fp_parts):
                    for i in range(len(fp_parts) - len(base_parts) + 1):
                        if fp_parts[i : i + len(base_parts)] == base_parts:
                            return True
    return False


def is_within_size_limit(filepath: str, max_mb: int) -> bool:
    """True if file size ≤ limit."""
    try:
        return os.path.getsize(filepath) <= max_mb * 1024 * 1024
    except OSError:
        return False


def passes_all(filepath: str, config: Dict[str, Any]) -> bool:
    """Combined gate — extension + exclusion + size."""
    if not is_supported(filepath):
        return False
    if is_excluded(filepath, config.get("exclude_patterns", [])):
        return False
    if not is_within_size_limit(filepath, config.get("max_file_size_mb", 50)):
        return False
    return True
