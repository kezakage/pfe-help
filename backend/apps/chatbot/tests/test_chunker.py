"""Unit tests for the text-chunking helpers."""
from apps.chatbot.services.chunker import split_text, tiptap_to_plain


def test_split_text_returns_empty_for_empty_input():
    assert split_text("") == []
    assert split_text("   ") == []


def test_split_text_keeps_short_text_as_single_chunk():
    short = "Une phrase courte."
    assert split_text(short, size=500) == [short]


def test_split_text_breaks_long_text_into_multiple_chunks():
    long = ("Première phrase. " * 50).strip()
    chunks = split_text(long, size=200, overlap=20)
    assert len(chunks) > 1
    # Each chunk should respect the size budget (with a small slack for overlap glue).
    for c in chunks:
        assert len(c) <= 260


def test_split_text_overlap_carries_context_between_chunks():
    text = (
        "Paragraphe A avec du contenu long. " * 10
        + "\n\n"
        + "Paragraphe B totalement différent. " * 10
    )
    chunks = split_text(text, size=200, overlap=40)
    assert len(chunks) >= 2
    # Subsequent chunks should begin with a slice of the previous chunk's tail.
    assert chunks[1].startswith(chunks[0][-40:].split()[0])


def test_tiptap_to_plain_extracts_text_from_nested_doc():
    doc = {
        "type": "doc",
        "content": [
            {"type": "heading", "content": [{"type": "text", "text": "Titre"}]},
            {"type": "paragraph", "content": [
                {"type": "text", "text": "Bonjour "},
                {"type": "text", "text": "le monde"},
            ]},
        ],
    }
    plain = tiptap_to_plain(doc)
    assert "Titre" in plain
    assert "Bonjour le monde" in plain


def test_tiptap_to_plain_handles_none_and_lists():
    assert tiptap_to_plain(None) == ""
    assert tiptap_to_plain([]) == ""
    assert "x" in tiptap_to_plain([{"type": "text", "text": "x"}])
