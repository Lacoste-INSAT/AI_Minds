"""
Synapsis Backend — File Parsers
Route files by extension → extract raw text.

Currently implemented (no heavy deps):
  .txt / .md  → UTF-8 read
  .json       → recursive key-value flattening

Optional (require extra packages):
  .pdf        → PyMuPDF  (pymupdf)
  .docx       → python-docx
  .jpg/.png   → pytesseract OCR
  .wav/.mp3   → faster-whisper
"""

from __future__ import annotations

import json
from pathlib import Path

import structlog

logger = structlog.get_logger(__name__)


def parse_file(file_path: str) -> str:
    """
    Parse a file and return its raw text content.
    Raises ``NotImplementedError`` for formats whose optional dependency
    is not installed.
    """
    ext = Path(file_path).suffix.lower()

    if ext in (".txt", ".md"):
        return _parse_text(file_path)
    if ext == ".json":
        return _parse_json(file_path)
    if ext == ".pdf":
        return _parse_pdf(file_path)
    if ext == ".docx":
        return _parse_docx(file_path)
    if ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff"):
        return _parse_image(file_path)
    if ext in (".wav", ".mp3", ".m4a", ".flac", ".ogg"):
        return _parse_audio(file_path)

    # Fallback: attempt plain-text read
    return _parse_text(file_path)


# ---------------------------------------------------------------------------
# Implemented parsers
# ---------------------------------------------------------------------------

def _parse_text(file_path: str) -> str:
    return Path(file_path).read_text(encoding="utf-8", errors="replace")


def _parse_json(file_path: str) -> str:
    data = json.loads(Path(file_path).read_text(encoding="utf-8"))
    return _flatten_json(data)


def _flatten_json(data, prefix: str = "") -> str:
    """Recursively flatten a JSON object into readable key: value lines."""
    lines: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, (dict, list)):
                lines.append(_flatten_json(value, full_key))
            else:
                lines.append(f"{full_key}: {value}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            lines.append(_flatten_json(item, f"{prefix}[{idx}]"))
    else:
        lines.append(f"{prefix}: {data}" if prefix else str(data))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optional-dependency parsers
# ---------------------------------------------------------------------------

def _parse_pdf(file_path: str) -> str:
    try:
        import fitz  # pymupdf
    except ImportError:
        raise NotImplementedError(
            "PDF parsing requires pymupdf.  Install with:  pip install pymupdf"
        )
    text_parts: list[str] = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)


def _parse_docx(file_path: str) -> str:
    try:
        from docx import Document  # python-docx
    except ImportError:
        raise NotImplementedError(
            "DOCX parsing requires python-docx.  Install with:  pip install python-docx"
        )
    doc = Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)


def _parse_image(file_path: str) -> str:
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        raise NotImplementedError(
            "Image OCR requires Pillow + pytesseract.  "
            "Install with:  pip install Pillow pytesseract"
        )
    image = Image.open(file_path)
    return pytesseract.image_to_string(image)


def _parse_audio(file_path: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise NotImplementedError(
            "Audio transcription requires faster-whisper.  "
            "Install with:  pip install faster-whisper"
        )
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(file_path)
    return " ".join(seg.text for seg in segments)
