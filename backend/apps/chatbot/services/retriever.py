"""
Retriever: cosine similarity search over KnowledgeChunk embeddings.

Uses pgvector's cosine distance operator (`<=>`); the HNSW index on
`embedding` makes this O(log N) for our corpus size.
"""
from __future__ import annotations

from pgvector.django import CosineDistance

from ..models import KnowledgeChunk
from .embeddings import embed_text


def retrieve(query: str, *, top_k: int = 5) -> list[KnowledgeChunk]:
    """
    Return the top-K chunks most similar to `query` by cosine similarity.

    Filters out chunks with no embedding (defensive — can happen if
    re-indexing was interrupted).
    """
    if not query or not query.strip():
        return []
    qvec = embed_text(query)
    qs = (
        KnowledgeChunk.objects.exclude(embedding__isnull=True)
        .annotate(distance=CosineDistance("embedding", qvec))
        .order_by("distance")[:top_k]
    )
    return list(qs)
