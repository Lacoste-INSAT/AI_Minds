"""
Synapsis Backend — Text Chunking (Person 3)
Sentence-aware chunking, 500-char default, 100-char overlap.

TODO (Person 3): Implement sentence-boundary-aware chunking.
"""

from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100,
) -> list[str]:
    """Split text into overlapping chunks at sentence boundaries."""
    raise NotImplementedError("Person 3: implement sentence-aware chunking")
