from rest_framework import serializers

from .models import ChatMessage, ChatSession, KnowledgeChunk


class ChunkCitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeChunk
        fields = ("id", "source_type", "source_id", "title", "url_path")


class ChatMessageSerializer(serializers.ModelSerializer):
    citations = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = (
            "id", "role", "content", "citations",
            "input_tokens", "output_tokens", "created_at",
        )

    def get_citations(self, obj):
        if not obj.citation_chunk_ids:
            return []
        chunks = KnowledgeChunk.objects.filter(id__in=obj.citation_chunk_ids)
        return ChunkCitationSerializer(chunks, many=True).data


class ChatSessionSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ("id", "title", "created_at", "updated_at", "messages")


class AskSerializer(serializers.Serializer):
    """Input payload for POST /chat/ask/."""
    message = serializers.CharField(min_length=2, max_length=2000)
    session_id = serializers.IntegerField(required=False, allow_null=True)
    anon_key = serializers.CharField(required=False, allow_blank=True, max_length=64)
