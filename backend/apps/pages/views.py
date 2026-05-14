from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.permissions import IsExpertOrReadOnly
from apps.heritage.models import Project, ProjectMember
from apps.heritage.permissions import IsProjectMemberOrReadOnlyPublic

from .models import Page, PageVersion
from .serializers import PageSerializer, PageVersionSerializer, PageVersionMiniSerializer


def _ensure_project_member(user, project: Project):
    if user.role == "admin":
        return
    if not ProjectMember.objects.filter(project=project, user=user).exists():
        raise PermissionDenied("You must be a project member to edit pages.")


class PageViewSet(viewsets.ModelViewSet):
    """Pages of a project (e.g. History, Architecture, Bibliography)."""
    serializer_class = PageSerializer
    permission_classes = (IsExpertOrReadOnly,)
    filterset_fields = ("project",)
    ordering_fields = ("position", "updated_at")

    def get_queryset(self):
        u = self.request.user
        qs = Page.objects.select_related("current_version", "current_version__author")
        project_id = self.request.query_params.get("project")
        if project_id:
            qs = qs.filter(project_id=project_id)
        if not u.is_authenticated:
            return qs.filter(project__status=Project.Status.PUBLISHED)
        if u.role == "admin":
            return qs
        from django.db.models import Q
        return qs.filter(
            Q(project__status=Project.Status.PUBLISHED)
            | Q(project__memberships__user=u)
        ).distinct()

    def perform_create(self, serializer):
        project = serializer.validated_data["project"]
        _ensure_project_member(self.request.user, project)
        serializer.save()


class PageVersionViewSet(viewsets.ModelViewSet):
    """
    Versions are append-only: creating a new one auto-increments
    `version_number`, sets `parent_version` to the current head, and bumps
    the page's pointer.

    Restoration: POST /pages/versions/{id}/restore/ creates a new version
    that copies the chosen one's content (Git-style "revert").
    """
    serializer_class = PageVersionSerializer
    permission_classes = (IsExpertOrReadOnly,)
    filterset_fields = ("page", "status", "author")
    ordering_fields = ("created_at", "version_number")

    def get_queryset(self):
        return (
            PageVersion.objects.select_related("page", "author", "discipline", "parent_version")
            .order_by("-created_at")
        )

    @transaction.atomic
    def perform_create(self, serializer):
        page = serializer.validated_data["page"] if "page" in serializer.validated_data else None
        # `page` is read-only on the serializer; require it via URL or body
        if page is None:
            page_id = self.request.data.get("page_id") or self.request.data.get("page")
            page = Page.objects.select_for_update().get(pk=page_id)

        _ensure_project_member(self.request.user, page.project)

        last = PageVersion.objects.filter(page=page).order_by("-version_number").first()
        next_number = (last.version_number + 1) if last else 1

        version = serializer.save(
            page=page,
            version_number=next_number,
            parent_version=last,
            author=self.request.user,
        )
        page.current_version = version
        page.save(update_fields=["current_version", "updated_at"])

    @action(detail=True, methods=["post"], url_path="restore")
    @transaction.atomic
    def restore(self, request, pk=None):
        old: PageVersion = self.get_object()
        _ensure_project_member(request.user, old.page.project)

        last = PageVersion.objects.filter(page=old.page).order_by("-version_number").first()
        version = PageVersion.objects.create(
            page=old.page,
            version_number=(last.version_number + 1) if last else 1,
            parent_version=last,
            content_json=old.content_json,
            change_summary=f"Restored from v{old.version_number}",
            author=request.user,
            discipline=old.discipline,
            status=PageVersion.Status.DRAFT,
        )
        old.page.current_version = version
        old.page.save(update_fields=["current_version", "updated_at"])
        return Response(PageVersionSerializer(version).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path=r"diff")
    def diff(self, request):
        """
        Return a shallow diff between two versions:
            GET /pages/versions/diff/?a=<id>&b=<id>
        Uses python's difflib on the JSON-serialized content.
        """
        from difflib import unified_diff
        import json

        a_id = request.query_params.get("a")
        b_id = request.query_params.get("b")
        if not (a_id and b_id):
            return Response({"detail": "a and b are required"}, status=400)
        a = PageVersion.objects.get(pk=a_id)
        b = PageVersion.objects.get(pk=b_id)
        a_text = json.dumps(a.content_json, ensure_ascii=False, indent=2).splitlines()
        b_text = json.dumps(b.content_json, ensure_ascii=False, indent=2).splitlines()
        diff = list(unified_diff(a_text, b_text, fromfile=f"v{a.version_number}", tofile=f"v{b.version_number}", lineterm=""))
        return Response({"diff": diff})

    @action(detail=False, methods=["get"], url_path=r"history/(?P<page_id>\d+)")
    def history(self, request, page_id=None):
        qs = PageVersion.objects.filter(page_id=page_id).order_by("-version_number")
        return Response(PageVersionMiniSerializer(qs, many=True).data)
