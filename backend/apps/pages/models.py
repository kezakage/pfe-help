"""
Pages & versions.

A Project owns ordered Pages (e.g. "History", "Architecture", "Bibliography").
Each Page has many PageVersions — full snapshots stored as a Tiptap/ProseMirror
JSON document. This delivers Git-like versioning: each version has a parent,
an author, a discipline (for color-coding), and a change_summary.

Per the simplified schema, contributor color-coding lives inside the
content_json (each block carries author_id / discipline_id), avoiding a
heavy CONTRIBUTION_BLOCK table.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.heritage.models import Project


class Page(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="pages")
    title = models.CharField(max_length=180)
    position = models.PositiveIntegerField(default=0, db_index=True)

    # Pointer to the currently active version
    current_version = models.ForeignKey(
        "PageVersion", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="+",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("project_id", "position")
        unique_together = ("project", "title")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.project.title} / {self.title}"


class PageVersion(models.Model):
    """Full snapshot of a page's content (Tiptap/ProseMirror JSON)."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    page = models.ForeignKey(Page, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    parent_version = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="children",
    )
    content_json = models.JSONField(default=dict, blank=True)

    change_summary = models.CharField(max_length=240, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="page_versions",
    )
    # Authoring discipline (used for color-coding the legend on the project)
    discipline = models.ForeignKey(
        "accounts.Discipline", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="page_versions",
    )

    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("page", "version_number")
        ordering = ("-created_at",)
        indexes = [models.Index(fields=["page", "version_number"])]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.page} v{self.version_number}"
