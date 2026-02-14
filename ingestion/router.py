"""
Router — dispatches a filepath to the correct parser based on extension.

Usage:
    from ingestion.router import route

    parser = route("notes.pdf")
    text = parser.parse("notes.pdf")
"""

from pathlib import Path
from typing import Dict, Type

# ---------------------------------------------------------------------------
# Extension → parser-module mapping
# ---------------------------------------------------------------------------
# Each value is a dotted import path *relative to ingestion.parsers*.
# Actual class imports are deferred so missing optional deps
# (pytesseract, faster-whisper …) don't blow up at import time.

_EXT_TO_PARSER: Dict[str, str] = {
    # PDF
    ".pdf":  "pdf_parser.PdfParser",
    # Plain text
    ".txt":  "text_parser.TextParser",
    ".md":   "text_parser.TextParser",
    ".json": "text_parser.TextParser",
    # Word documents
    ".docx": "docx_parser.DocxParser",
    # Images (OCR)
    ".jpg":  "image_parser.ImageParser",
    ".jpeg": "image_parser.ImageParser",
    ".png":  "image_parser.ImageParser",
    # Audio (transcription)
    ".wav":  "audio_parser.AudioParser",
    ".mp3":  "audio_parser.AudioParser",
}

SUPPORTED_EXTENSIONS = set(_EXT_TO_PARSER.keys())


class UnsupportedFileType(Exception):
    """Raised when a file's extension has no registered parser."""


def _import_parser(dotted: str):
    """
    Lazily import a parser class from ingestion.parsers.

    Parameters
    ----------
    dotted : str
        e.g. "pdf_parser.PdfParser"

    Returns
    -------
    type
        The parser class.
    """
    module_name, class_name = dotted.rsplit(".", 1)
    full_module = f"ingestion.parsers.{module_name}"

    import importlib
    mod = importlib.import_module(full_module)
    return getattr(mod, class_name)


def route(filepath: str):
    """
    Return the parser class responsible for the given file.

    Parameters
    ----------
    filepath : str
        Path to the file (only the extension matters).

    Returns
    -------
    parser class
        An uninstantiated class with a `parse(filepath) -> str` method.

    Raises
    ------
    UnsupportedFileType
        If the extension is not in the routing table.
    """
    ext = Path(filepath).suffix.lower()

    if ext not in _EXT_TO_PARSER:
        raise UnsupportedFileType(
            f"No parser registered for '{ext}' (file: {filepath})"
        )

    return _import_parser(_EXT_TO_PARSER[ext])


def get_parser_name(filepath: str) -> str:
    """
    Return a human-readable parser label without importing anything.

    Useful for logging/display before actually loading heavy deps.
    """
    ext = Path(filepath).suffix.lower()
    dotted = _EXT_TO_PARSER.get(ext)
    if dotted is None:
        return "unknown"
    return dotted.rsplit(".", 1)[1]   # e.g. "PdfParser"
