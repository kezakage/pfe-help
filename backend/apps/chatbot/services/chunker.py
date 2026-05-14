"""
Text chunking utilities.

Heritage descriptions and Tiptap pages can be long; we split them into
~500-char chunks with a small overlap so retrieval can return tight,
relevant snippets without dropping context across boundaries.
"""
from __future__ import annotations

import re

DEFAULT_CHUNK_SIZE = 500
DEFAULT_OVERLAP = 80


def split_text(text: str, *, size: int = DEFAULT_CHUNK_SIZE, overlap: int = DEFAULT_OVERLAP) -> list[str]:
    """
    Split `text` into chunks of approximately `size` characters, breaking on
    sentence/whitespace boundaries when possible. Adjacent chunks share an
    `overlap` of trailing characters so context is never sliced mid-thought.
    """
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]

    # Split on paragraph then sentence boundaries to avoid mid-word cuts.
    paragraphs = re.split(r"\n{2,}", text)
    pieces: list[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) <= size:
            pieces.append(para)
            continue
        sentences = re.split(r"(?<=[.!?؟])\s+", para)
        buf = ""
        for s in sentences:
            if len(buf) + len(s) + 1 <= size:
                buf = f"{buf} {s}".strip()
            else:
                if buf:
                    pieces.append(buf)
                if len(s) > size:
                    # Hard split a too-long sentence on whitespace.
                    words = s.split()
                    chunk = ""
                    for w in words:
                        if len(chunk) + len(w) + 1 <= size:
                            chunk = f"{chunk} {w}".strip()
                        else:
                            if chunk:
                                pieces.append(chunk)
                            chunk = w
                    if chunk:
                        buf = chunk
                    else:
                        buf = ""
                else:
                    buf = s
        if buf:
            pieces.append(buf)

    # Apply overlap so consecutive chunks share trailing context.
    if overlap <= 0 or len(pieces) <= 1:
        return pieces
    out: list[str] = []
    for i, p in enumerate(pieces):
        if i == 0:
            out.append(p)
            continue
        prev_tail = pieces[i - 1][-overlap:] if len(pieces[i - 1]) > overlap else pieces[i - 1]
        out.append(f"{prev_tail} {p}".strip())
    return out


def tiptap_to_plain(doc: dict | list | None) -> str:
    """Walk a Tiptap JSON document and concatenate visible text."""
    if not doc:
        return ""
    if isinstance(doc, list):
        return "\n\n".join(tiptap_to_plain(n) for n in doc)
    if not isinstance(doc, dict):
        return ""

    if doc.get("type") == "text":
        return doc.get("text", "")
    if doc.get("type") in {"hard_break", "hardBreak"}:
        return "\n"

    parts: list[str] = []
    for child in doc.get("content", []) or []:
        parts.append(tiptap_to_plain(child))

    node_type = doc.get("type")
    if node_type in {"paragraph", "heading", "list_item", "listItem", "blockquote"}:
        return "".join(parts) + "\n\n"
    if node_type in {"bullet_list", "bulletList", "ordered_list", "orderedList"}:
        return "".join(parts)
    return "".join(parts)
