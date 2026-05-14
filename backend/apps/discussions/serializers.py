from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import ConflictVote, Discussion, Message


class MessageSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id", "discussion", "author", "body", "parent",
            "is_proposal", "created_at", "edited_at",
        )
        read_only_fields = ("author", "created_at", "edited_at")


class DiscussionSerializer(serializers.ModelSerializer):
    opened_by = UserMiniSerializer(read_only=True)
    resolved_by = UserMiniSerializer(read_only=True)
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Discussion
        fields = (
            "id", "project", "page", "related_version",
            "title", "type", "status",
            "opened_by", "resolved_by",
            "created_at", "updated_at", "resolved_at",
            "message_count",
        )
        read_only_fields = ("opened_by", "resolved_by", "resolved_at",
                            "created_at", "updated_at")

    def get_message_count(self, obj):
        return obj.messages.count()


class ConflictVoteSerializer(serializers.ModelSerializer):
    voter = UserMiniSerializer(read_only=True)

    class Meta:
        model = ConflictVote
        fields = (
            "id", "discussion", "proposal", "voter",
            "choice", "comment", "created_at",
        )
        read_only_fields = ("voter", "created_at")
