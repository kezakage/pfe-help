"""
RAG orchestration: retrieve relevant chunks, build a prompt, call Claude.

When `ANTHROPIC_API_KEY` is unset (CI / offline demos), the service falls
back to a deterministic stub that lists the retrieved sources — useful so
the UI keeps working without a paid key, and so tests can run hermetically.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from django.conf import settings

from ..models import KnowledgeChunk
from .retriever import retrieve

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Tu es l'assistant documentaire de PatrimoineHub, la plateforme nationale \
algérienne dédiée au patrimoine architectural. Réponds en français, de \
manière précise et concise, en t'appuyant EXCLUSIVEMENT sur les extraits \
fournis dans le contexte. Si l'information n'est pas dans le contexte, \
dis-le honnêtement plutôt que d'inventer. Cite les sources en fin de \
réponse en mentionnant les titres des notices.\
"""


@dataclass
class RagAnswer:
    text: str
    sources: list[KnowledgeChunk]
    input_tokens: int = 0
    output_tokens: int = 0
    model: str = ""


def _format_context(chunks: list[KnowledgeChunk], max_chars: int) -> str:
    """Concatenate retrieved chunks into a tagged context block, capped."""
    parts: list[str] = []
    used = 0
    for i, c in enumerate(chunks, start=1):
        block = f"[{i}] {c.title}\n{c.text}\n"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)
    return "\n".join(parts)


def _stub_answer(question: str, chunks: list[KnowledgeChunk]) -> str:
    """Deterministic fallback when no API key is configured."""
    if not chunks:
        return (
            "Je n'ai pas trouvé d'information pertinente dans la base "
            f"documentaire pour répondre à : « {question} »."
        )
    lines = [
        "Réponse simulée (clé Anthropic non configurée — la plateforme renvoie "
        "directement les passages les plus pertinents) :",
        "",
    ]
    for i, c in enumerate(chunks, start=1):
        snippet = c.text[:240].rstrip()
        if len(c.text) > 240:
            snippet += "…"
        lines.append(f"[{i}] {c.title} — {snippet}")
    return "\n".join(lines)


def ask(question: str) -> RagAnswer:
    """Run the full RAG cycle for one user turn."""
    top_k = getattr(settings, "CHATBOT_TOP_K", 5)
    max_chars = getattr(settings, "CHATBOT_MAX_CONTEXT_CHARS", 6000)
    chunks = retrieve(question, top_k=top_k)

    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    model = getattr(settings, "ANTHROPIC_MODEL", "claude-haiku-4-5")

    if not api_key:
        return RagAnswer(
            text=_stub_answer(question, chunks),
            sources=chunks,
            model="stub",
        )

    context = _format_context(chunks, max_chars=max_chars)
    user_msg = (
        f"Contexte (extraits de la base PatrimoineHub) :\n\n"
        f"{context}\n\n"
        f"Question de l'utilisateur : {question}"
    )

    try:
        from anthropic import Anthropic
    except Exception as exc:  # noqa: BLE001
        logger.exception("Anthropic SDK import failed: %s", exc)
        return RagAnswer(text=_stub_answer(question, chunks), sources=chunks, model="stub")

    client = Anthropic(api_key=api_key)
    try:
        resp = client.messages.create(
            model=model,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Anthropic API call failed: %s", exc)
        return RagAnswer(text=_stub_answer(question, chunks), sources=chunks, model="stub")

    text = ""
    for block in getattr(resp, "content", []) or []:
        if getattr(block, "type", None) == "text":
            text += getattr(block, "text", "")
    usage = getattr(resp, "usage", None)
    return RagAnswer(
        text=text.strip() or _stub_answer(question, chunks),
        sources=chunks,
        input_tokens=getattr(usage, "input_tokens", 0) if usage else 0,
        output_tokens=getattr(usage, "output_tokens", 0) if usage else 0,
        model=model,
    )
