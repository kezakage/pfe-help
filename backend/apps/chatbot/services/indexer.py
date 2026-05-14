"""
Indexer: walks the heritage corpus and refreshes KnowledgeChunk rows.

We index three sources:
  - HeritageResource.description (per monument)
  - Project.title + Project.description (per project)
  - PageVersion.content_json (Tiptap → plain text, current version of each Page)

The indexer is idempotent: chunks are upserted on `chunk_key`, so calling
`reindex()` twice does not duplicate rows.
"""
from __future__ import annotations

import logging

from django.db import transaction

from apps.heritage.models import HeritageResource, Project
from apps.pages.models import Page

from ..models import KnowledgeChunk
from .chunker import split_text, tiptap_to_plain
from .embeddings import embed_batch

logger = logging.getLogger(__name__)


def _build_chunks_for_resource(r: HeritageResource) -> list[dict]:
    text = (r.description or "").strip()
    if not text:
        return []
    metadata = {
        "wilaya": r.wilaya,
        "commune": r.commune,
        "period": r.period,
        "architectural_type": r.architectural_type,
        "classification_level": r.classification_level,
    }
    title = r.name_fr
    url_path = f"/explorer/{r.id}"
    chunks = split_text(text)
    return [
        {
            "source_type": KnowledgeChunk.SourceType.HERITAGE_RESOURCE,
            "source_id": r.id,
            "source_field": "description",
            "chunk_key": f"heritage_resource:{r.id}:description:{i}",
            "text": chunk,
            "title": title,
            "url_path": url_path,
            "metadata": metadata,
        }
        for i, chunk in enumerate(chunks)
    ]


def _build_chunks_for_project(p: Project) -> list[dict]:
    pieces = []
    if p.title:
        pieces.append(p.title)
    if p.description:
        pieces.append(p.description)
    text = "\n\n".join(pieces).strip()
    if not text:
        return []
    metadata = {
        "status": p.status,
        "resource_id": p.resource_id,
        "resource_name": p.resource.name_fr if p.resource_id else "",
    }
    chunks = split_text(text)
    return [
        {
            "source_type": KnowledgeChunk.SourceType.PROJECT,
            "source_id": p.id,
            "source_field": "description",
            "chunk_key": f"project:{p.id}:description:{i}",
            "text": chunk,
            "title": p.title,
            "url_path": f"/projet/{p.id}",
            "metadata": metadata,
        }
        for i, chunk in enumerate(chunks)
    ]


def _build_chunks_for_page(page: Page) -> list[dict]:
    cv = page.current_version
    if not cv or not cv.content_json:
        return []
    text = tiptap_to_plain(cv.content_json).strip()
    if not text:
        return []
    chunks = split_text(text)
    return [
        {
            "source_type": KnowledgeChunk.SourceType.PAGE_VERSION,
            "source_id": cv.id,
            "source_field": "content_json",
            "chunk_key": f"page_version:{cv.id}:content_json:{i}",
            "text": chunk,
            "title": f"{page.project.title} — {page.title}",
            "url_path": f"/projet/{page.project_id}",
            "metadata": {
                "project_id": page.project_id,
                "page_id": page.id,
                "page_title": page.title,
                "version": cv.version_number if hasattr(cv, "version_number") else None,
            },
        }
        for i, chunk in enumerate(chunks)
    ]


def collect_chunks() -> list[dict]:
    """Walk the corpus and produce a flat list of chunk dicts (no embeddings yet)."""
    out: list[dict] = []
    for r in HeritageResource.objects.all().iterator():
        out.extend(_build_chunks_for_resource(r))
    for p in Project.objects.select_related("resource").all().iterator():
        out.extend(_build_chunks_for_project(p))
    for page in Page.objects.select_related("current_version", "project").all().iterator():
        out.extend(_build_chunks_for_page(page))
    return out


@transaction.atomic
def reindex(*, batch_size: int = 32) -> dict:
    """
    Re-embed every chunk in the corpus and upsert into KnowledgeChunk.
    Old chunks whose chunk_key no longer matches any source are deleted.
    """
    chunks = collect_chunks()
    logger.info("Indexer: %d chunks to embed", len(chunks))

    # Embed in batches.
    if chunks:
        texts = [c["text"] for c in chunks]
        embeddings: list[list[float]] = []
        for i in range(0, len(texts), batch_size):
            embeddings.extend(embed_batch(texts[i : i + batch_size]))
        for c, e in zip(chunks, embeddings):
            c["embedding"] = e

    # Upsert.
    seen_keys: set[str] = set()
    for c in chunks:
        seen_keys.add(c["chunk_key"])
        KnowledgeChunk.objects.update_or_create(
            chunk_key=c["chunk_key"],
            defaults={
                "source_type": c["source_type"],
                "source_id": c["source_id"],
                "source_field": c["source_field"],
                "text": c["text"],
                "title": c["title"],
                "url_path": c["url_path"],
                "metadata": c["metadata"],
                "embedding": c["embedding"],
            },
        )

    # Drop stale chunks (their source no longer exists or text changed).
    deleted, _ = (
        KnowledgeChunk.objects.exclude(chunk_key__in=seen_keys).delete()
        if seen_keys
        else KnowledgeChunk.objects.all().delete()
    )

    return {"indexed": len(chunks), "deleted": deleted}
