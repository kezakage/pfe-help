from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import Annotation, Media
from .serializers import (
    AnnotationSerializer,
    AnnotationWriteSerializer,
    MediaSerializer,
    MediaUploadSerializer,
)


class MediaViewSet(viewsets.ModelViewSet):
    queryset = Media.objects.select_related("uploader", "project").all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filterset_fields = ["project", "media_type", "uploader"]
    search_fields = ["caption"]
    ordering_fields = ["created_at", "size_bytes"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return MediaUploadSerializer
        return MediaSerializer

    def perform_create(self, serializer):
        media = serializer.save(uploader=self.request.user)
        # async thumbnail generation + CLIP annotation
        try:
            from .tasks import annotate_image, generate_thumbnail
            generate_thumbnail.delay(media.id)
            if media.media_type == Media.Type.IMAGE:
                annotate_image.delay(media.id)
        except Exception:
            pass

    @extend_schema(
        summary="List annotations attached to a media",
        description=(
            "Returns all annotations (manual and AI-generated) for the given media, "
            "including author, discipline, geometry (bounding box), and validation status. "
            "AI-generated annotations from CLIP zero-shot classification are flagged "
            "with `is_ai_generated=true` and may be unvalidated by experts."
        ),
        responses={200: AnnotationSerializer(many=True)},
        tags=["media"],
    )
    @action(detail=True, methods=["get"])
    def annotations(self, request, pk=None):
        media = self.get_object()
        qs = media.annotations.select_related("author", "discipline").all()
        return Response(AnnotationSerializer(qs, many=True, context={"request": request}).data)


class AnnotationViewSet(viewsets.ModelViewSet):
    queryset = Annotation.objects.select_related(
        "author", "discipline", "media", "resource", "validated_by",
    ).all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ["media", "resource", "is_ai_generated", "is_validated", "discipline"]
    ordering_fields = ["created_at"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return AnnotationWriteSerializer
        return AnnotationSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @extend_schema(
        summary="Validate an AI-generated annotation",
        description=(
            "Marks an annotation as expert-validated, recording the validating user. "
            "Typically applied to AI-generated annotations (CLIP) once an expert has "
            "reviewed the suggested label and bounding box."
        ),
        request=None,
        responses={200: AnnotationSerializer},
        tags=["media"],
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def validate_annotation(self, request, pk=None):
        """Validate an AI-generated annotation."""
        annotation = self.get_object()
        annotation.is_validated = True
        annotation.validated_by = request.user
        annotation.save(update_fields=["is_validated", "validated_by"])
        return Response(AnnotationSerializer(annotation, context={"request": request}).data)

    @extend_schema(
        summary="Reject an AI-generated annotation",
        description=(
            "Deletes an AI-generated annotation that an expert deemed incorrect. "
            "Returns HTTP 400 if the annotation is not AI-generated — manual annotations "
            "must be deleted through the standard DELETE endpoint instead."
        ),
        request=None,
        responses={204: None, 400: None},
        tags=["media"],
    )
    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        """Reject (delete) an AI-generated annotation."""
        annotation = self.get_object()
        if not annotation.is_ai_generated:
            return Response(
                {"detail": "Only AI-generated annotations can be rejected via this endpoint."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        annotation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
