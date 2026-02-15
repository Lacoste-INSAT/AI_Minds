"""
ingestion.processor — chunking and embedding utilities.
"""

from .chunker import chunk_documents
from .embedder import embed_chunks

__all__ = ["chunk_documents", "embed_chunks"]
