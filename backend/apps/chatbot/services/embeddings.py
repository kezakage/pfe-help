"""
Embedding service.

Wraps a sentence-transformers multilingual model. The model is loaded
lazily on first use (cold start ~2-3 s) and shared across calls.
"""
from __future__ import annotations

import logging
import threading

from django.conf import settings

logger = logging.getLogger(__name__)

_model = None
_lock = threading.Lock()


def get_model():
    """
    Return the embedding model singleton. Loaded lazily so the Django
    startup time is not penalised when chatbot features are unused.
    """
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is None:  # double-checked locking
            from sentence_transformers import SentenceTransformer
            name = settings.EMBEDDING_MODEL_NAME
            logger.info("Loading embedding model: %s", name)
            _model = SentenceTransformer(name)
    return _model


def embed_text(text: str) -> list[float]:
    """Embed a single string to a 768-dim float vector."""
    model = get_model()
    vec = model.encode([text], normalize_embeddings=True, convert_to_numpy=True)[0]
    return vec.tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Embed many strings in one batched forward pass — much faster."""
    if not texts:
        return []
    model = get_model()
    vecs = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        batch_size=16,
        show_progress_bar=False,
    )
    return [v.tolist() for v in vecs]
