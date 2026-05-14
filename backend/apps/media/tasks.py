"""
Celery tasks for media processing.

  - generate_thumbnail: extracts a thumbnail and image dimensions for an image upload.
  - annotate_image: runs CLIP zero-shot classification, stores top tags and creates
    a pending Annotation suggesting the dominant label (requires expert validation).
"""
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task
def generate_thumbnail(media_id: int):
    """Generate a thumbnail for an image media (no-op for video/document for now)."""
    from io import BytesIO

    from django.core.files.base import ContentFile

    from .models import Media

    try:
        media = Media.objects.get(pk=media_id)
    except Media.DoesNotExist:
        return

    if media.media_type != Media.Type.IMAGE:
        return

    try:
        from PIL import Image
    except ImportError:
        # Pillow not installed — skip silently
        return

    try:
        media.file.open("rb")
        img = Image.open(media.file)
        media.width, media.height = img.size

        img.thumbnail((400, 400))
        buffer = BytesIO()
        fmt = (img.format or "JPEG")
        img.save(buffer, format=fmt)
        buffer.seek(0)

        thumb_name = f"thumb_{media.pk}.{fmt.lower()}"
        media.thumbnail.save(thumb_name, ContentFile(buffer.read()), save=False)
        media.save(update_fields=["width", "height", "thumbnail"])
    except Exception:
        # Don't crash the worker on a bad image
        return
    finally:
        try:
            media.file.close()
        except Exception:
            pass


@shared_task
def annotate_image(media_id: int):
    """
    Run CLIP zero-shot classification on an image media and persist the top
    tags into `ai_tags`. Also creates a pending AI Annotation with the top
    label so an expert can validate or reject it from the UI.
    """
    from .models import Annotation, Media

    try:
        media = Media.objects.get(pk=media_id)
    except Media.DoesNotExist:
        return

    if media.media_type != Media.Type.IMAGE:
        media.ai_status = Media.AiStatus.SKIPPED
        media.save(update_fields=["ai_status"])
        return

    try:
        from .services.clip_classifier import classify_image
    except ImportError:
        logger.warning("CLIP classifier unavailable — sentence-transformers not installed?")
        media.ai_status = Media.AiStatus.FAILED
        media.save(update_fields=["ai_status"])
        return

    try:
        media.file.open("rb")
        data = media.file.read()
        tags = classify_image(data, top_k=3, min_score=0.10)
    except Exception as exc:
        logger.exception("CLIP annotation failed for media %s: %s", media_id, exc)
        media.ai_status = Media.AiStatus.FAILED
        media.save(update_fields=["ai_status"])
        return
    finally:
        try:
            media.file.close()
        except Exception:
            pass

    media.ai_tags = tags
    media.ai_status = Media.AiStatus.DONE
    media.save(update_fields=["ai_tags", "ai_status"])

    # Best-effort: create a pending Annotation for the top label so it shows
    # up in the validation queue. Falls back silently if uploader cannot be
    # used as author (FK/permission edge cases).
    if tags:
        try:
            top = tags[0]
            Annotation.objects.create(
                media=media,
                body_text=f"IA (CLIP) : {top['label']} — {int(top['score'] * 100)}%",
                author=media.uploader,
                is_ai_generated=True,
                is_validated=False,
            )
        except Exception as exc:
            logger.warning("Could not create AI annotation for media %s: %s", media_id, exc)
