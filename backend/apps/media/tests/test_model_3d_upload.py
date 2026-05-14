"""
Tests for the 3D model media type.

The MODEL_3D type was added so that experts can attach GLB/GLTF assets to a
project (e.g. photogrammetry of a Casbah courtyard) and view them with
<model-viewer> in the workspace. Validation rules:

  * extension must be .glb or .gltf  OR  mime must be model/gltf-*
  * size must stay under MAX_MODEL_3D_BYTES (50 MB)
  * thumbnail / CLIP tasks must skip the asset (they only target images)
"""
from django.core.files.uploadedfile import SimpleUploadedFile
import pytest

from apps.media.models import Media
from apps.media.serializers import MAX_MODEL_3D_BYTES
from apps.media.tasks import annotate_image, generate_thumbnail

pytestmark = pytest.mark.django_db


# A minimal but valid GLB header: magic "glTF" + version 2 + length.
# `model-viewer` won't actually render this, but the serializer only inspects
# extension / mime / size, so a few bytes are enough for upload tests.
_GLB_HEADER = b"glTF\x02\x00\x00\x00\x14\x00\x00\x00" + b"\x00" * 8


def _glb_file(name="casbah.glb", content_type="model/gltf-binary", size=None):
    payload = _GLB_HEADER if size is None else (b"\x00" * size)
    return SimpleUploadedFile(name, payload, content_type=content_type)


# ---------------------------------------------------------------------------
# Upload happy-paths
# ---------------------------------------------------------------------------
def test_upload_glb_succeeds(auth_client, expert_user, project_published):
    client = auth_client(expert_user)
    res = client.post(
        "/api/v1/media/",
        {
            "project": project_published.id,
            "media_type": Media.Type.MODEL_3D,
            "file": _glb_file(),
        },
        format="multipart",
    )
    assert res.status_code == 201, res.content
    body = res.json()
    assert body["media_type"] == "model_3d"
    assert body["file"].endswith(".glb") or ".glb" in body["file"]
    # And the read serializer (GET detail) exposes file_url
    detail = client.get(f"/api/v1/media/{body['id']}/").json()
    assert detail["file_url"].endswith(".glb") or ".glb" in detail["file_url"]


def test_upload_gltf_extension_succeeds(auth_client, expert_user, project_published):
    """Even with a generic mime type, the .gltf extension is accepted."""
    client = auth_client(expert_user)
    res = client.post(
        "/api/v1/media/",
        {
            "project": project_published.id,
            "media_type": Media.Type.MODEL_3D,
            "file": SimpleUploadedFile(
                "casbah.gltf", b'{"asset":{"version":"2.0"}}',
                content_type="application/octet-stream",
            ),
        },
        format="multipart",
    )
    assert res.status_code == 201


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def test_upload_rejects_non_glb_when_type_is_model_3d(auth_client, expert_user, project_published):
    client = auth_client(expert_user)
    res = client.post(
        "/api/v1/media/",
        {
            "project": project_published.id,
            "media_type": Media.Type.MODEL_3D,
            "file": SimpleUploadedFile("plan.pdf", b"%PDF-1.4", content_type="application/pdf"),
        },
        format="multipart",
    )
    assert res.status_code == 400
    assert "file" in res.json()


def test_upload_rejects_oversized_3d_model(auth_client, expert_user, project_published):
    client = auth_client(expert_user)
    too_big = MAX_MODEL_3D_BYTES + 1
    res = client.post(
        "/api/v1/media/",
        {
            "project": project_published.id,
            "media_type": Media.Type.MODEL_3D,
            "file": _glb_file(size=too_big),
        },
        format="multipart",
    )
    assert res.status_code == 400


# ---------------------------------------------------------------------------
# Async tasks must not touch 3D models
# ---------------------------------------------------------------------------
@pytest.fixture
def model_3d_media(expert_user, project_published):
    return Media.objects.create(
        project=project_published,
        uploader=expert_user,
        media_type=Media.Type.MODEL_3D,
        file=_glb_file(),
        mime_type="model/gltf-binary",
    )


def test_thumbnail_task_skips_3d_model(model_3d_media):
    # generate_thumbnail returns silently for non-image media; assert no
    # side-effect on width/height/thumbnail.
    generate_thumbnail(model_3d_media.id)
    model_3d_media.refresh_from_db()
    assert model_3d_media.width is None
    assert model_3d_media.height is None
    assert not model_3d_media.thumbnail


def test_clip_task_marks_3d_model_skipped(model_3d_media):
    annotate_image(model_3d_media.id)
    model_3d_media.refresh_from_db()
    assert model_3d_media.ai_status == Media.AiStatus.SKIPPED
    assert model_3d_media.ai_tags == []


# ---------------------------------------------------------------------------
# Filtering
# ---------------------------------------------------------------------------
def test_media_list_can_filter_by_model_3d(auth_client, expert_user, project_published):
    Media.objects.create(
        project=project_published, uploader=expert_user,
        media_type=Media.Type.IMAGE,
        file=SimpleUploadedFile("a.png", b"\x89PNG\r\n", content_type="image/png"),
    )
    Media.objects.create(
        project=project_published, uploader=expert_user,
        media_type=Media.Type.MODEL_3D,
        file=_glb_file(),
    )
    client = auth_client(expert_user)
    res = client.get(f"/api/v1/media/?project={project_published.id}&media_type=model_3d")
    assert res.status_code == 200
    items = res.json().get("results", res.json())
    assert len(items) == 1
    assert items[0]["media_type"] == "model_3d"
