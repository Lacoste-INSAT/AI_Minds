"""
Synapsis Backend — Text Chunking
Sentence-aware chunking with configurable size and overlap.
"""

from __future__ import annotations

import re


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """
    Split *text* into overlapping chunks, breaking at sentence boundaries
    whenever possible.

    Algorithm:
    1. Split the text into sentences using punctuation heuristics.
    2. Accumulate sentences into a chunk until adding the next sentence
       would exceed *chunk_size* characters.
    3. Emit the chunk; start the next chunk with the last *overlap*
       characters of the previous chunk for context continuity.
    4. If a single sentence is longer than *chunk_size*, force-split it
       at *chunk_size* boundaries.
    """
    if not text or not text.strip():
        return []

    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # Handle sentences longer than chunk_size by force-splitting
        if len(sentence) > chunk_size:
            # First, flush whatever we have
            if current.strip():
                chunks.append(current.strip())
                current = ""

            # Force-split the long sentence
            for i in range(0, len(sentence), chunk_size - overlap):
                fragment = sentence[i : i + chunk_size]
                if fragment.strip():
                    chunks.append(fragment.strip())
            continue

        # Would adding this sentence exceed the limit?
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) > chunk_size and current.strip():
            chunks.append(current.strip())

            # Overlap: seed next chunk with tail of current
            if overlap > 0 and len(current) > overlap:
                current = current[-overlap:].lstrip() + " " + sentence
            else:
                current = sentence
        else:
            current = candidate

    if current.strip():
        chunks.append(current.strip())

    return chunks
