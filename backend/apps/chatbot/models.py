"""
Chatbot RAG models.

`KnowledgeChunk` stores embedded content snippets used at retrieval time.
`ChatSession` and `ChatMessage` capture conversation history (anonymous
sessions are also persisted, keyed by an opaque session token).
"""
from __future__ import annotations

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from pgvector.django import HnswIndex, VectorField

# Dim of paraphrase-multilingual-mpnet-base-v2 (FR + AR capable, 768 dims).
EMBEDDING_DIM = 768


class KnowledgeChunk(models.Model):
    """
    A single retrievable snippet, indexed by cosine similarity.

    Chunks are produced by the indexer from HeritageResource descriptions,
    Project metadata, and PageVersion Tiptap content.
    """

    class SourceType(models.TextChoices):
        HERITAGE_RESOURCE = "heritage_resource", _("Heritage resource")
        PROJECT = "project", _("Project")
        PAGE_VERSION = "page_version", _("Page version")

    source_type = models.CharField(max_length=24, choices=SourceType.choices, db_index=True)
    source_id = models.PositiveIntegerField(db_index=True)
    source_field = models.CharField(max_length=64, blank=True)

    # Stable identifier for upserts (source_type:source_id:source_field:position).
    chunk_key = models.CharField(max_length=200, unique=True)

    text = models.TextField()
    embedding = VectorField(dimensions=EMBEDDING_DIM, null=True, blank=True)

    # User-facing pointer: name to show when citing the chunk + URL to navigate.
    title = models.CharField(max_length=240, blank=True)
    url_path = models.CharField(max_length=240, blank=True)

    # Free-form metadata (wilaya, period, classification, ...).
    metadata = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("source_type", "source_id")
        indexes = [
            models.Index(fields=["source_type", "source_id"]),
            HnswIndex(
                name="kc_embedding_hnsw",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.source_type}:{self.source_id} — {self.title or self.text[:40]}"


class ChatSession(models.Model):
    """
    A conversation thread. `user` is null for anonymous public visitors;
    in that case `anon_key` (a random opaque token issued to the browser)
    distinguishes one anonymous visitor's history from another's.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="chat_sessions",
    )
    anon_key = models.CharField(max_length=64, blank=True, db_index=True)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)


class ChatMessage(models.Model):
    """One user/assistant turn within a ChatSession."""

    class Role(models.TextChoices):
        USER = "user", _("User")
        ASSISTANT = "assistant", _("Assistant")
        SYSTEM = "system", _("System")

    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=12, choices=Role.choices)
    content = models.TextField()

    # IDs of KnowledgeChunks cited by the assistant — empty for user/system turns.
    citation_chunk_ids = models.JSONField(default=list, blank=True)

    # Tokens consumed by the LLM call (assistant turns only).
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=["session", "created_at"])]
