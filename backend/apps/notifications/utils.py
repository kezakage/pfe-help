"""
Helpers to create notifications + push them over WebSocket.
"""
from typing import Iterable

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


def _push_to_user(user_id: int, payload: dict) -> None:
    layer = get_channel_layer()
    if layer is None:
        return
    try:
        async_to_sync(layer.group_send)(
            f"user_{user_id}",
            {"type": "notify", "data": payload},
        )
    except Exception:
        pass


def push(recipient, *, type: str, title: str, body: str = "", url: str = "", payload: dict | None = None) -> Notification:
    notif = Notification.objects.create(
        recipient=recipient,
        type=type,
        title=title,
        body=body,
        url=url,
        payload=payload or {},
    )
    _push_to_user(recipient.pk, {
        "id": notif.pk,
        "type": notif.type,
        "title": notif.title,
        "body": notif.body,
        "url": notif.url,
        "payload": notif.payload,
        "created_at": notif.created_at.isoformat(),
    })
    return notif


def push_many(recipients: Iterable, **kwargs) -> list[Notification]:
    return [push(r, **kwargs) for r in recipients]


# ---------- specialized helpers ----------

def notify_expert_decision(user, *, approved: bool) -> None:
    """Push when an admin approves or rejects an expert account request."""
    if approved:
        push(
            user,
            type=Notification.Type.EXPERT_VALIDATED,
            title="Statut expert validé",
            body="Votre demande a été approuvée. Vous accédez maintenant aux outils de l'espace expert.",
            url="/app/profil",
        )
    else:
        push(
            user,
            type=Notification.Type.EXPERT_REJECTED,
            title="Statut expert refusé",
            body="Votre demande de statut expert a été refusée. Contactez l'équipe pour plus d'informations.",
            url="/app/profil",
        )


def notify_project_published(project) -> None:
    """Push to every project member when the project transitions to published."""
    recipients = list(project.members.all())
    if not recipients:
        return
    push_many(
        recipients,
        type=Notification.Type.VERSION_PUBLISHED,
        title=f"Projet publié — {project.title}",
        body="Le projet vient d'être publié et est maintenant visible publiquement.",
        url=f"/projets-publics/{project.resource_id}" if project.resource_id else f"/app/projets/{project.pk}",
        payload={"project_id": project.pk},
    )


def notify_discussion_message(message) -> None:
    """Notify all participants of a discussion (except author)."""
    discussion = message.discussion
    project = discussion.project
    recipients = set()
    for member in project.members.all():
        if member.pk != message.author_id:
            recipients.add(member)
    if discussion.opened_by_id != message.author_id:
        recipients.add(discussion.opened_by)
    if not recipients:
        return
    push_many(
        recipients,
        type=Notification.Type.DISCUSSION_MESSAGE,
        title=f"Nouveau message — {discussion.title}",
        body=message.body[:200],
        url=f"/app/projects/{project.pk}/discussion/{discussion.pk}",
        payload={
            "discussion_id": discussion.pk,
            "message_id": message.pk,
            "project_id": project.pk,
        },
    )
