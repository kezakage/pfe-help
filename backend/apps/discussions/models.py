"""
Discussions: chat threads attached to a project (or a page/version), with
optional conflict resolution flow + simple votes.
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.heritage.models import Project
from apps.pages.models import Page, PageVersion


class Discussion(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        RESOLVED = "resolved", _("Resolved")
        ARCHIVED = "archived", _("Archived")

    class Type(models.TextChoices):
        GENERAL = "general", _("General")
        CONFLICT = "conflict", _("Editorial conflict")
        REVIEW = "review", _("Review")

    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="discussions",
    )
    page = models.ForeignKey(
        Page, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="discussions",
    )
    related_version = models.ForeignKey(
        PageVersion, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="discussions",
    )

    title = models.CharField(max_length=200)
    type = models.CharField(max_length=12, choices=Type.choices, default=Type.GENERAL)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)

    opened_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="opened_discussions",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="resolved_discussions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["type", "status"]),
        ]


class Message(models.Model):
    discussion = models.ForeignKey(
        Discussion, on_delete=models.CASCADE, related_name="messages",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="discussion_messages",
    )
    body = models.TextField()
    parent = models.ForeignKey(
        "self", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="replies",
    )
    is_proposal = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("created_at",)
        indexes = [models.Index(fields=["discussion", "created_at"])]


class ConflictVote(models.Model):
    """Simple unweighted vote on a proposal message inside a CONFLICT discussion."""

    class Choice(models.TextChoices):
        APPROVE = "approve", _("Approve")
        REJECT = "reject", _("Reject")
        ABSTAIN = "abstain", _("Abstain")

    discussion = models.ForeignKey(
        Discussion, on_delete=models.CASCADE, related_name="votes",
    )
    proposal = models.ForeignKey(
        Message, null=True, blank=True,
        on_delete=models.CASCADE, related_name="votes",
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name="conflict_votes",
    )
    choice = models.CharField(max_length=10, choices=Choice.choices)
    comment = models.CharField(max_length=240, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.UniqueConstraint(
                fields=["discussion", "voter"],
                name="one_vote_per_user_per_discussion",
            ),
        ]
