"""
ingestion.parsers — file-type-specific text extraction.

Each parser implements BaseParser.parse(filepath) -> str.
"""

from .base import BaseParser

__all__ = ["BaseParser"]
