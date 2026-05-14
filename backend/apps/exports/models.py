"""
Asynchronous export jobs (PDF / ZIP / GeoJSON).

A user requests an export of a project (or selection); a Celery worker fills
in the file URL when ready and flips the status.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.heritage.models import Project


class ExportJob(models.Model):
    class Format(models.TextChoices):
        PDF = "pdf", _("PDF")
        ZIP = "zip", _("ZIP archive")
        GEOJSON = "geojson", _("GeoJSON")
        CSV = "csv", _("CSV")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        PROCESSING = "processing", _("Processing")
        DONE = "done", _("Done")
        FAILED = "failed", _("Failed")

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="export_jobs",
    )
    project = models.ForeignKey(
        Project, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="export_jobs",
    )

    format = models.CharField(max_length=10, choices=Format.choices)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)

    # Optional filters/options the user picked, e.g. {"include_media": true}
    options = models.JSONField(default=dict, blank=True)

    # Filled in by the worker
    file = models.FileField(upload_to="exports/%Y/%m/", null=True, blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["status", "created_at"])]
