"""
Tests for notification push hooks:
  - notify_expert_decision() / notify_project_published() helpers
  - the validate/publish endpoints that wire them in
"""
import pytest

from apps.accounts.models import User
from apps.heritage.models import Project, ProjectMember
from apps.notifications.models import Notification
from apps.notifications.utils import notify_expert_decision, notify_project_published

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helper-level tests
# ---------------------------------------------------------------------------
def test_notify_expert_approved_creates_validated_notification(pending_expert):
    notify_expert_decision(pending_expert, approved=True)

    notif = Notification.objects.get(recipient=pending_expert)
    assert notif.type == Notification.Type.EXPERT_VALIDATED
    assert "validé" in notif.title.lower() or "approuv" in notif.body.lower()
    assert notif.url


def test_notify_expert_rejected_creates_rejected_notification(pending_expert):
    notify_expert_decision(pending_expert, approved=False)

    notif = Notification.objects.get(recipient=pending_expert)
    assert notif.type == Notification.Type.EXPERT_REJECTED


def test_notify_project_published_pushes_one_notification_per_member(
    project_draft, researcher_user
):
    # Add a second member so we can verify push_many fans out correctly.
    ProjectMember.objects.create(
        project=project_draft,
        user=researcher_user,
        project_role=ProjectMember.ProjectRole.CONTRIBUTOR,
    )

    notify_project_published(project_draft)

    notifs = Notification.objects.filter(type=Notification.Type.VERSION_PUBLISHED)
    assert notifs.count() == project_draft.members.count() == 2
    # Each member should receive exactly one.
    recipient_ids = set(notifs.values_list("recipient_id", flat=True))
    member_ids = set(project_draft.members.values_list("pk", flat=True))
    assert recipient_ids == member_ids


def test_notify_project_published_with_no_members_is_a_noop(project_draft):
    # Strip members and confirm nothing is created.
    project_draft.members.clear()
    notify_project_published(project_draft)
    assert Notification.objects.count() == 0


# ---------------------------------------------------------------------------
# Endpoint-level tests — verify the hook fires when the view runs
# ---------------------------------------------------------------------------
def test_validate_endpoint_approve_triggers_notification(
    auth_client, admin_user, pending_expert
):
    client = auth_client(admin_user)
    res = client.post(
        f"/api/v1/auth/admin/users/{pending_expert.pk}/validate/",
        {"decision": "approve"},
        format="json",
    )
    assert res.status_code == 200, res.content

    # User status updated AND notification created
    pending_expert.refresh_from_db()
    assert pending_expert.status == User.Status.ACTIVE
    assert Notification.objects.filter(
        recipient=pending_expert,
        type=Notification.Type.EXPERT_VALIDATED,
    ).count() == 1


def test_validate_endpoint_reject_triggers_rejection_notification(
    auth_client, admin_user, pending_expert
):
    client = auth_client(admin_user)
    res = client.post(
        f"/api/v1/auth/admin/users/{pending_expert.pk}/validate/",
        {"decision": "reject"},
        format="json",
    )
    assert res.status_code == 200, res.content

    pending_expert.refresh_from_db()
    assert pending_expert.status == User.Status.REJECTED
    assert Notification.objects.filter(
        recipient=pending_expert,
        type=Notification.Type.EXPERT_REJECTED,
    ).count() == 1


def test_publish_endpoint_notifies_all_members(
    auth_client, expert_user, researcher_user, project_draft
):
    # Add a second member so we can verify multi-recipient delivery.
    ProjectMember.objects.create(
        project=project_draft,
        user=researcher_user,
        project_role=ProjectMember.ProjectRole.CONTRIBUTOR,
    )

    client = auth_client(expert_user)
    res = client.post(f"/api/v1/heritage/projects/{project_draft.pk}/publish/")
    assert res.status_code == 200, res.content

    project_draft.refresh_from_db()
    assert project_draft.status == Project.Status.PUBLISHED
    notifs = Notification.objects.filter(type=Notification.Type.VERSION_PUBLISHED)
    assert notifs.count() == 2
    assert set(notifs.values_list("recipient_id", flat=True)) == {
        expert_user.pk, researcher_user.pk,
    }


def test_publish_endpoint_does_not_double_notify_on_repeat_publish(
    auth_client, expert_user, project_published
):
    """Re-publishing an already published project must not spam notifications."""
    client = auth_client(expert_user)
    # First call: project is already PUBLISHED (per fixture), so no notif expected.
    res = client.post(f"/api/v1/heritage/projects/{project_published.pk}/publish/")
    assert res.status_code == 200, res.content
    assert Notification.objects.filter(
        type=Notification.Type.VERSION_PUBLISHED
    ).count() == 0
