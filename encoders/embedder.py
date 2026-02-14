"""
Embedder — Sentence-Transformers wrapper for all-MiniLM-L6-v2.

Produces 384-dim embeddings. Runs 100% local, no API calls.
"""

import logging
from typing import Union

import numpy as np

logger = logging.getLogger(__name__)

_model = None


def _load_model(model_name: str):
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading embedding model: {model_name}")
        _model = SentenceTransformer(model_name)
        logger.info("Embedding model ready")
    return _model


class Embedder:
    """Lightweight wrapper around sentence-transformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = _load_model(model_name)
        self._dimension = self._model.get_sentence_embedding_dimension()

    @property
    def dimension(self) -> int:
        return self._dimension

    def encode(self, text: str) -> list[float]:
        """Encode a single string → list of floats."""
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def encode_batch(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Encode many strings at once (much faster than one-by-one)."""
        vecs = self._model.encode(texts, batch_size=batch_size, normalize_embeddings=True)
        return [v.tolist() for v in vecs]
