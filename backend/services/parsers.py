"""
Synapsis Backend — File Parsers (Person 3)
Route files by extension → extract raw text.
Supported: TXT, MD, PDF (PyMuPDF), images (pytesseract), audio (faster-whisper),
           JSON, DOCX.

TODO (Person 3): Implement all parsers.
"""

from __future__ import annotations


def parse_file(file_path: str) -> str:
    """
    Parse a file and return its raw text content.

    Routing by extension:
    - .txt / .md  → read UTF-8
    - .pdf        → PyMuPDF
    - .png/.jpg   → pytesseract OCR
    - .mp3/.wav   → faster-whisper transcription
    - .json       → flatten keys
    - .docx       → python-docx
    """
    raise NotImplementedError("Person 3: implement file parsers")
