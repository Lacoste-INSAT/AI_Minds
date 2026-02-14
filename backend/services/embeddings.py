"""
Synapsis Backend — Embeddings Service
Uses sentence-transformers all-MiniLM-L6-v2 (384-dim, local).
"""

from __future__ import annotations

import numpy as np
import structlog

from backend.config import settings

logger = structlog.get_logger(__name__)

_model = None


def _get_model():
    """Lazy-load the sentence-transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        logger.info("embeddings.loading_model", model=settings.embedding_model)
        _model = SentenceTransformer(settings.embedding_model)
        logger.info("embeddings.model_loaded", model=settings.embedding_model, dim=settings.embedding_dim)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single text string, returns 384-dim vector."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts. Returns list of 384-dim vectors."""
    if not texts:
        return []
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
    return embeddings.tolist()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot / (norm_a * norm_b))
