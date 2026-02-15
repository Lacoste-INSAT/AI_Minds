"""
ingestion.parsers — file-type-specific text extraction + normalisation.

Each parser implements BaseParser.parse(filepath) -> str.
The Content Normalizer (normalizer.py) cleans raw parser output.
"""

from .base import BaseParser
from .normalizer import normalise

__all__ = ["BaseParser", "normalise"]
