"""Plain-text extraction for .txt, .md, and .json files."""

import json
import logging
from pathlib import Path

from .base import BaseParser

logger = logging.getLogger("synapsis.parsers.text")

# Encodings to try in order
_ENCODINGS = ("utf-8", "utf-8-sig", "latin-1", "cp1252")


class TextParser(BaseParser):
    """Read text-based files with encoding fallback."""

    @staticmethod
    def parse(filepath: str) -> str:
        """
        Read file contents as text.

        For .json files the content is pretty-printed so downstream
        chunking sees readable text instead of compressed JSON.

        Parameters
        ----------
        filepath : str
            Path to a .txt, .md, or .json file.

        Returns
        -------
        str
            File contents as a string.
        """
        text = TextParser._read_with_fallback(filepath)

        if Path(filepath).suffix.lower() == ".json":
            text = TextParser._prettify_json(text)

        logger.info("Text parsed: %s (%d chars)", filepath, len(text))
        return text

    # ------------------------------------------------------------------

    @staticmethod
    def _read_with_fallback(filepath: str) -> str:
        """Try multiple encodings, return text from the first that works."""
        for enc in _ENCODINGS:
            try:
                with open(filepath, "r", encoding=enc) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                continue

        logger.warning("All encodings failed for %s — reading as latin-1", filepath)
        with open(filepath, "r", encoding="latin-1") as f:
            return f.read()

    @staticmethod
    def _prettify_json(raw: str) -> str:
        """Pretty-print JSON so it's readable after chunking."""
        try:
            data = json.loads(raw)
            return json.dumps(data, indent=2, ensure_ascii=False)
        except json.JSONDecodeError:
            return raw
