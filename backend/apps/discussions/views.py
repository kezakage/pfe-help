from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import ConflictVote, Discussion, Message
from .serializers import ConflictVoteSerializer, DiscussionSerializer, MessageSerializer


class DiscussionViewSet(viewsets.ModelViewSet):
    queryset = Discussion.objects.select_related(
        "project", "page", "related_version", "opened_by", "resolved_by",
    ).all()
    serializer_class = DiscussionSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["project", "page", "type", "status"]
    search_fields = ["title"]
    ordering_fields = ["created_at", "updated_at"]

    def perform_create(self, serializer):
        serializer.save(opened_by=self.request.user)

    @action(detail=True, methods=["get", "post"])
    def messages(self, request, pk=None):
        discussion = self.get_object()
        if request.method == "GET":
            qs = discussion.messages.select_related("author", "parent").all()
            return Response(MessageSerializer(qs, many=True).data)

        ser = MessageSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        msg = ser.save(author=request.user, discussion=discussion)
        # touch updated_at
        discussion.save(update_fields=["updated_at"])
        # push notification (best-effort)
        try:
            from apps.notifications.utils import notify_discussion_message
            notify_discussion_message(msg)
        except Exception:
            pass
        return Response(MessageSerializer(msg).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def resolve(self, request, pk=None):
        discussion = self.get_object()
        discussion.status = Discussion.Status.RESOLVED
        discussion.resolved_by = request.user
        discussion.resolved_at = timezone.now()
        discussion.save(update_fields=["status", "resolved_by", "resolved_at"])
        return Response(DiscussionSerializer(discussion).data)

    @action(detail=True, methods=["get", "post"])
    def votes(self, request, pk=None):
        discussion = self.get_object()
        if request.method == "GET":
            qs = discussion.votes.select_related("voter", "proposal").all()
            return Response(ConflictVoteSerializer(qs, many=True).data)

        ser = ConflictVoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        # upsert: one vote per user per discussion
        ConflictVote.objects.update_or_create(
            discussion=discussion,
            voter=request.user,
            defaults={
                "choice": ser.validated_data["choice"],
                "comment": ser.validated_data.get("comment", ""),
                "proposal": ser.validated_data.get("proposal"),
            },
        )
        return Response(self._tally(discussion))

    @action(detail=True, methods=["get"])
    def tally(self, request, pk=None):
        return Response(self._tally(self.get_object()))

    @staticmethod
    def _tally(discussion):
        counts = {"approve": 0, "reject": 0, "abstain": 0}
        for v in discussion.votes.all():
            counts[v.choice] = counts.get(v.choice, 0) + 1
        counts["total"] = sum(counts[k] for k in ("approve", "reject", "abstain"))
        return counts


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.select_related("author", "discussion", "parent").all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["discussion", "is_proposal", "author"]

    def perform_create(self, serializer):
        msg = serializer.save(author=self.request.user)
        msg.discussion.save(update_fields=["updated_at"])

    def perform_update(self, serializer):
        serializer.save(edited_at=timezone.now())
