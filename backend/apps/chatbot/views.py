"""
Chatbot endpoints.

Two surfaces:
  - POST /api/v1/chat/ask/         — single-shot Q/A (anon-friendly).
  - GET/DELETE /api/v1/chat/sessions/ — authenticated session history.

Anonymous callers may pass `anon_key` (an opaque token stored in browser
localStorage) so their history is groupable without any account.
"""
from __future__ import annotations

from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ChatMessage, ChatSession
from .serializers import (
    AskSerializer,
    ChatMessageSerializer,
    ChatSessionSerializer,
)
from .services.rag import ask as rag_ask
from .throttling import ChatAnonRateThrottle, ChatUserRateThrottle


def _get_or_create_session(*, user, anon_key: str, session_id: int | None) -> ChatSession:
    """Fetch the requested session (scoped to the caller) or create a new one."""
    if session_id:
        qs = ChatSession.objects.filter(pk=session_id)
        if user and user.is_authenticated:
            qs = qs.filter(user=user)
        else:
            qs = qs.filter(user__isnull=True, anon_key=anon_key or "")
        session = qs.first()
        if session:
            return session

    return ChatSession.objects.create(
        user=user if (user and user.is_authenticated) else None,
        anon_key="" if (user and user.is_authenticated) else (anon_key or ""),
    )


class AskView(APIView):
    """POST a question, get an answer with citations."""

    permission_classes = [permissions.AllowAny]
    throttle_classes = [ChatAnonRateThrottle, ChatUserRateThrottle]

    @extend_schema(
        summary="Ask the heritage chatbot a question",
        description=(
            "Runs a retrieval-augmented generation (RAG) cycle: retrieves relevant "
            "chunks from the heritage knowledge base, asks Claude for a grounded answer, "
            "and persists both turns in the chat session. Anonymous callers may pass "
            "`anon_key` (an opaque token stored in browser localStorage) so their history "
            "is groupable without an account. Rate-limited per user/IP."
        ),
        request=AskSerializer,
        responses={
            200: inline_serializer(
                name="AskResponse",
                fields={
                    "session_id": serializers.IntegerField(),
                    "user_message": ChatMessageSerializer(),
                    "assistant_message": ChatMessageSerializer(),
                    "model": serializers.CharField(),
                },
            ),
        },
        examples=[
            OpenApiExample(
                "Ask about Casbah",
                value={"message": "Quelle est l'histoire de la Casbah d'Alger ?"},
            ),
        ],
        tags=["chatbot"],
    )
    def post(self, request):
        ser = AskSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        message = ser.validated_data["message"]
        session_id = ser.validated_data.get("session_id")
        anon_key = ser.validated_data.get("anon_key", "") or ""

        user = request.user if request.user.is_authenticated else None
        session = _get_or_create_session(user=user, anon_key=anon_key, session_id=session_id)

        # Persist user turn first so it's there even if the LLM call later errors.
        user_msg = ChatMessage.objects.create(
            session=session, role=ChatMessage.Role.USER, content=message,
        )

        answer = rag_ask(message)

        assistant_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.ASSISTANT,
            content=answer.text,
            citation_chunk_ids=[c.id for c in answer.sources],
            input_tokens=answer.input_tokens,
            output_tokens=answer.output_tokens,
        )

        # Use first user question as session title (truncated) the first time.
        if not session.title:
            session.title = message[:80]
            session.save(update_fields=["title", "updated_at"])
        else:
            session.save(update_fields=["updated_at"])

        return Response(
            {
                "session_id": session.id,
                "user_message": ChatMessageSerializer(user_msg).data,
                "assistant_message": ChatMessageSerializer(assistant_msg).data,
                "model": answer.model,
            },
            status=status.HTTP_200_OK,
        )


class ChatSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """List / retrieve / delete the authenticated user's chat sessions."""

    serializer_class = ChatSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "delete", "head", "options"]

    def get_queryset(self):
        return (
            ChatSession.objects
            .filter(user=self.request.user)
            .prefetch_related("messages")
        )

    def destroy(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
