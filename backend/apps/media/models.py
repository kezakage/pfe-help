"""
Media files (images, videos, documents) and Annotations.

Per the simplified schema, ANNOTATION is a single table; either `media`
or `resource` is set (image/map annotations both go through the same model).
"""
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.heritage.models import HeritageResource, Project


class Media(models.Model):
    class Type(models.TextChoices):
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        DOCUMENT = "document", _("Document")
        MODEL_3D = "model_3d", _("3D model")

    project = models.ForeignKey(
        Project, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="media",
    )
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="uploaded_media",
    )

    media_type = models.CharField(max_length=10, choices=Type.choices, db_index=True)
    file = models.FileField(upload_to="uploads/%Y/%m/")  # served via S3 if USE_S3=1

    mime_type = models.CharField(max_length=80, blank=True)
    size_bytes = models.PositiveBigIntegerField(default=0)

    # image/video metadata
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)

    thumbnail = models.ImageField(upload_to="thumbnails/%Y/%m/", null=True, blank=True)

    caption = models.CharField(max_length=255, blank=True)
    license = models.CharField(max_length=120, blank=True)

    geo_point = gis_models.PointField(geography=True, null=True, blank=True)

    # CNN auto-annotation (CLIP zero-shot)
    # Format: [{"label": "mosquée", "score": 0.87}, ...]
    ai_tags = models.JSONField(default=list, blank=True)

    class AiStatus(models.TextChoices):
        PENDING = "pending", _("Pending")
        DONE = "done", _("Done")
        FAILED = "failed", _("Failed")
        SKIPPED = "skipped", _("Skipped")  # non-image files

    ai_status = models.CharField(
        max_length=8,
        choices=AiStatus.choices,
        default=AiStatus.PENDING,
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["media_type", "created_at"])]


class Annotation(models.Model):
    """
    Either:
      - `media` is set → image annotation (geometry_json holds rectangle/polygon)
      - `resource` is set → cartographic annotation (geo_point is the marker)
    """

    media = models.ForeignKey(
        Media, null=True, blank=True,
        on_delete=models.CASCADE, related_name="annotations",
    )
    resource = models.ForeignKey(
        HeritageResource, null=True, blank=True,
        on_delete=models.CASCADE, related_name="annotations",
    )

    geometry_json = models.JSONField(default=dict, blank=True)
    geo_point = gis_models.PointField(geography=True, null=True, blank=True)

    body_text = models.TextField(blank=True)

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="annotations",
    )
    discipline = models.ForeignKey(
        "accounts.Discipline", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="annotations",
    )

    # AI annotations require human validation before being "published"
    is_ai_generated = models.BooleanField(default=False)
    is_validated = models.BooleanField(default=True)
    validated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="validated_annotations",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["media", "created_at"]),
            models.Index(fields=["resource", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                name="annotation_target_required",
                check=(
                    models.Q(media__isnull=False, resource__isnull=True)
                    | models.Q(media__isnull=True, resource__isnull=False)
                ),
            )
        ]

    def clean(self):
        if not self.media and not self.resource:
            raise ValidationError("Annotation must reference either a media or a heritage resource.")
        if self.media and self.resource:
            raise ValidationError("Annotation cannot reference both a media and a resource.")
