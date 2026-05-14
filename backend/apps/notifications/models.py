"""
In-app notifications, also broadcast over WebSocket via Channels.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Notification(models.Model):
    class Type(models.TextChoices):
        DISCUSSION_MESSAGE = "discussion_message", _("New discussion message")
        VERSION_PUBLISHED = "version_published", _("Page version published")
        ANNOTATION_VALIDATED = "annotation_validated", _("Annotation validated")
        EXPORT_READY = "export_ready", _("Export ready")
        EXPERT_VALIDATED = "expert_validated", _("Expert account validated")
        EXPERT_REJECTED = "expert_rejected", _("Expert account rejected")
        PROJECT_INVITE = "project_invite", _("Project invitation")
        SYSTEM = "system", _("System")

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=32, choices=Type.choices)

    # Free-form payload referenced by the frontend (project_id, message_id, ...)
    payload = models.JSONField(default=dict, blank=True)

    title = models.CharField(max_length=180)
    body = models.TextField(blank=True)
    url = models.CharField(max_length=300, blank=True)

    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["recipient", "is_read", "created_at"])]
