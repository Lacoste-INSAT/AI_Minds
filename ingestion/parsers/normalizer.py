"""
Content Normalizer (CLEAN) — Parsing & Normalization Module.

Diagram node:  TXT/OCR/AUD → **CLEAN** → META (Cognitive Enrichment)

Sits between raw parser output and the chunker / enrichment pipeline.
Cleans encoding artefacts, normalises whitespace, and produces uniform
plain-text ready for chunking + embedding.
"""

import re
import unicodedata
import logging
from typing import Optional

logger = logging.getLogger("synapsis.normalizer")


def normalise(raw: str) -> str:
    """
    Full content normalisation pipeline.

    Steps
    -----
    1. Unicode NFC normalisation (combine accented characters)
    2. Strip BOM / zero-width characters
    3. Normalise line endings (CRLF → LF)
    4. Replace exotic whitespace (NBSP, thin space, etc.) with regular space
    5. Collapse 3+ blank lines into a single paragraph break (\\n\\n)
    6. Collapse horizontal whitespace runs within lines
    7. Remove control characters (except \\n and \\t)
    8. Strip leading / trailing whitespace

    Parameters
    ----------
    raw : str
        Raw text from any parser (TextParser, ImageParser, AudioParser …).

    Returns
    -------
    str
        Cleaned, uniform plain-text.
    """
    if not raw:
        return ""

    text = raw

    # 1. Unicode NFC
    text = unicodedata.normalize("NFC", text)

    # 2. Strip BOM + zero-width chars
    text = text.lstrip("\ufeff")
    text = re.sub(r"[\u200b\u200c\u200d\u2060\ufeff]", "", text)

    # 3. Normalise line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # 4. Replace exotic whitespace with regular space
    #    Covers: NBSP, EN/EM space, thin space, hair space, figure space, etc.
    text = re.sub(
        r"[\u00a0\u2000-\u200a\u202f\u205f\u3000]",
        " ",
        text,
    )

    # 5. Collapse 3+ blank lines → double newline (paragraph break)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Collapse horizontal whitespace within lines
    text = re.sub(r"[^\S\n]+", " ", text)

    # 7. Remove control characters (keep \n and \t)
    text = re.sub(r"[^\S \n\t]", "", text)

    # 8. Strip
    text = text.strip()

    logger.debug("Normalised: %d → %d chars", len(raw), len(text))
    return text
