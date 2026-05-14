"""
Tests for the CLIP annotation Celery task.

The CLIP model is heavy (~600MB) — we monkey-patch `classify_image` so the
test doesn't actually run inference. This validates the wiring (status
transitions, tag persistence, AI Annotation creation, error handling)
without needing the model on disk.
"""
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.media.models import Annotation, Media
from apps.media.tasks import annotate_image

pytestmark = pytest.mark.django_db


def _png_bytes() -> bytes:
    """Return a tiny valid PNG so PIL doesn't choke if real classify is hit."""
    from PIL import Image
    buf = BytesIO()
    Image.new("RGB", (16, 16), (180, 80, 40)).save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def image_media(expert_user):
    return Media.objects.create(
        uploader=expert_user,
        media_type=Media.Type.IMAGE,
        file=SimpleUploadedFile("t.png", _png_bytes(), content_type="image/png"),
        mime_type="image/png",
    )


@pytest.fixture
def doc_media(expert_user):
    return Media.objects.create(
        uploader=expert_user,
        media_type=Media.Type.DOCUMENT,
        file=SimpleUploadedFile("t.pdf", b"%PDF-1.4 fake", content_type="application/pdf"),
        mime_type="application/pdf",
    )


def test_annotate_image_skips_non_image_media(doc_media):
    annotate_image(doc_media.id)
    doc_media.refresh_from_db()
    assert doc_media.ai_status == Media.AiStatus.SKIPPED
    assert doc_media.ai_tags == []
    assert Annotation.objects.filter(media=doc_media).count() == 0


def test_annotate_image_persists_tags_and_creates_annotation(image_media, monkeypatch):
    fake_tags = [
        {"label": "mosquée", "score": 0.62},
        {"label": "minaret", "score": 0.21},
    ]
    monkeypatch.setattr(
        "apps.media.tasks.classify_image",
        lambda data, **kw: fake_tags,
        raising=False,
    )
    # Re-import to bind the monkeypatched symbol where the task imports it.
    import apps.media.services.clip_classifier as cc
    monkeypatch.setattr(cc, "classify_image", lambda data, **kw: fake_tags)

    annotate_image(image_media.id)

    image_media.refresh_from_db()
    assert image_media.ai_status == Media.AiStatus.DONE
    assert image_media.ai_tags == fake_tags

    ann = Annotation.objects.get(media=image_media, is_ai_generated=True)
    assert ann.is_validated is False
    assert "mosquée" in ann.body_text
    assert "62%" in ann.body_text


def test_annotate_image_marks_failed_on_classifier_exception(image_media, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("model not available")

    import apps.media.services.clip_classifier as cc
    monkeypatch.setattr(cc, "classify_image", boom)

    annotate_image(image_media.id)
    image_media.refresh_from_db()
    assert image_media.ai_status == Media.AiStatus.FAILED
    assert image_media.ai_tags == []
    assert Annotation.objects.filter(media=image_media).count() == 0


def test_annotate_image_handles_missing_media():
    # Should not raise when the media id no longer exists.
    annotate_image(99_999_999)


def test_media_serializer_exposes_ai_fields(api_client, expert_user, auth_client, monkeypatch):
    """Verify ai_tags + ai_status are returned by the API."""
    import apps.media.services.clip_classifier as cc
    monkeypatch.setattr(cc, "classify_image", lambda data, **kw: [{"label": "casbah", "score": 0.9}])

    media = Media.objects.create(
        uploader=expert_user,
        media_type=Media.Type.IMAGE,
        file=SimpleUploadedFile("t.png", _png_bytes(), content_type="image/png"),
        mime_type="image/png",
    )
    annotate_image(media.id)

    client = auth_client(expert_user)
    res = client.get(f"/api/v1/media/{media.id}/")
    assert res.status_code == 200
    body = res.json()
    assert body["ai_status"] == "done"
    assert body["ai_tags"] == [{"label": "casbah", "score": 0.9}]
