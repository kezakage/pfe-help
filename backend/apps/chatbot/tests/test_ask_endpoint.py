"""
Endpoint tests for /api/v1/chat/ask/.

These run in stub mode (no Anthropic key configured) — the RAG service falls
back to listing retrieved chunks. Embedding is monkey-patched to a constant
vector so tests don't load the 400MB sentence-transformer model in CI.
"""
import pytest

from apps.chatbot.models import ChatMessage, ChatSession, KnowledgeChunk

pytestmark = pytest.mark.django_db


@pytest.fixture
def patch_embedder(monkeypatch):
    """Stub embed_text to return a fixed unit vector (avoids loading the model)."""
    def _fake(text: str):
        return [0.0] * 768

    # Patch in both the embeddings module AND the retriever's local import.
    import apps.chatbot.services.embeddings as emb
    import apps.chatbot.services.retriever as ret
    monkeypatch.setattr(emb, "embed_text", _fake)
    monkeypatch.setattr(ret, "embed_text", _fake)


@pytest.fixture
def seed_chunk(db):
    return KnowledgeChunk.objects.create(
        source_type=KnowledgeChunk.SourceType.HERITAGE_RESOURCE,
        source_id=1,
        chunk_key="heritage_resource:1:description:0",
        text="La Casbah d'Alger, médina ottomane inscrite UNESCO.",
        embedding=[0.0] * 768,
        title="Casbah d'Alger",
        url_path="/explorer/1",
    )


def test_ask_endpoint_creates_session_and_messages(api_client, patch_embedder, seed_chunk, settings):
    settings.ANTHROPIC_API_KEY = ""  # force stub mode
    res = api_client.post(
        "/api/v1/chat/ask/",
        {"message": "Parle-moi de la Casbah d'Alger.", "anon_key": "anon123"},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert body["model"] == "stub"
    assert body["session_id"]
    assert body["user_message"]["role"] == "user"
    assert body["assistant_message"]["role"] == "assistant"
    # Session and both messages persisted.
    session = ChatSession.objects.get(pk=body["session_id"])
    assert session.anon_key == "anon123"
    assert session.user is None
    assert session.messages.count() == 2


def test_ask_endpoint_validates_message_length(api_client):
    res = api_client.post("/api/v1/chat/ask/", {"message": "x"}, format="json")
    assert res.status_code == 400


def test_ask_endpoint_reuses_existing_session(api_client, patch_embedder, seed_chunk, settings):
    settings.ANTHROPIC_API_KEY = ""
    first = api_client.post(
        "/api/v1/chat/ask/",
        {"message": "Première question Casbah.", "anon_key": "anonX"},
        format="json",
    ).json()
    sid = first["session_id"]

    second = api_client.post(
        "/api/v1/chat/ask/",
        {"message": "Question de suivi.", "session_id": sid, "anon_key": "anonX"},
        format="json",
    ).json()
    assert second["session_id"] == sid
    assert ChatMessage.objects.filter(session_id=sid).count() == 4


def test_ask_endpoint_authenticated_user_owns_session(
    api_client, auth_client, expert_user, patch_embedder, seed_chunk, settings,
):
    settings.ANTHROPIC_API_KEY = ""
    client = auth_client(expert_user)
    res = client.post(
        "/api/v1/chat/ask/",
        {"message": "Question authentifiée."},
        format="json",
    )
    assert res.status_code == 200
    sid = res.json()["session_id"]
    session = ChatSession.objects.get(pk=sid)
    assert session.user_id == expert_user.id
    assert session.anon_key == ""


def test_sessions_endpoint_requires_authentication(api_client):
    res = api_client.get("/api/v1/chat/sessions/")
    assert res.status_code in (401, 403)


def test_sessions_endpoint_lists_only_caller_sessions(
    api_client, auth_client, expert_user, researcher_user, patch_embedder, seed_chunk, settings,
):
    settings.ANTHROPIC_API_KEY = ""
    expert_client = auth_client(expert_user)
    researcher_client = auth_client(researcher_user)
    expert_client.post("/api/v1/chat/ask/", {"message": "Question expert."}, format="json")
    researcher_client.post("/api/v1/chat/ask/", {"message": "Question chercheur."}, format="json")

    res = expert_client.get("/api/v1/chat/sessions/")
    assert res.status_code == 200
    body = res.json()
    items = body if isinstance(body, list) else body.get("results", [])
    assert len(items) == 1
    assert items[0]["title"].startswith("Question expert")
