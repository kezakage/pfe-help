from django.utils import timezone
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Discipline, User
from .permissions import IsAdmin, IsSelfOrAdmin
from .serializers import (
    DisciplineSerializer,
    RegisterSerializer,
    TokenSerializer,
    UserSerializer,
    ValidateExpertSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = TokenSerializer


class RefreshView(TokenRefreshView):
    pass


class RegisterView(viewsets.GenericViewSet):
    """POST /auth/register/ — public sign-up."""
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeViewSet(viewsets.GenericViewSet):
    """GET/PATCH /auth/me/ — current user profile."""
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def list(self, request):
        return Response(UserSerializer(request.user).data)

    def partial_update(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class DisciplineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Discipline.objects.all()
    serializer_class = DisciplineSerializer
    permission_classes = (IsAuthenticated,)


class UserAdminViewSet(viewsets.ModelViewSet):
    """
    Admin-only management of users. Includes the `validate` action which
    handles the workflow:
        - approve  → status=ACTIVE, sets validated_by/at
        - reject   → status=REJECTED
    """
    queryset = User.objects.all().order_by("-created_at")
    serializer_class = UserSerializer
    permission_classes = (IsAdmin,)
    filterset_fields = ("role", "status")
    search_fields = ("email", "first_name", "last_name", "institution_name")

    @extend_schema(
        summary="Approve or reject an expert account request",
        description=(
            "Admin-only. Transitions a user's `status` to either `ACTIVE` (on approve) or "
            "`REJECTED` (on reject). On success, a real-time WebSocket notification is "
            "pushed to the user via `/ws/notifications/` so the frontend can display a toast."
        ),
        request=ValidateExpertSerializer,
        responses={200: UserSerializer},
        examples=[
            OpenApiExample("Approve", value={"decision": "approve"}),
            OpenApiExample("Reject", value={"decision": "reject", "note": "Profil incomplet"}),
        ],
        tags=["admin"],
    )
    @action(detail=True, methods=["post"], url_path="validate")
    def validate(self, request, pk=None):
        user = self.get_object()
        ser = ValidateExpertSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        approved = ser.validated_data["decision"] == "approve"
        if approved:
            user.status = User.Status.ACTIVE
            user.validated_by = request.user
            user.validated_at = timezone.now()
        else:
            user.status = User.Status.REJECTED
        user.save(update_fields=["status", "validated_by", "validated_at"])

        # Push real-time WS notification to the user being validated.
        try:
            from apps.notifications.utils import notify_expert_decision
            notify_expert_decision(user, approved=approved)
        except Exception:
            pass
        return Response(UserSerializer(user).data)

    @action(detail=True, methods=["post"], url_path="suspend")
    def suspend(self, request, pk=None):
        user = self.get_object()
        user.status = User.Status.REJECTED
        user.is_active = False
        user.save(update_fields=["status", "is_active"])
        return Response(UserSerializer(user).data)


class AdminStatsView(APIView):
    """
    GET /auth/admin/stats/
    Admin-only aggregated platform statistics:
      - user counts by status
      - project / discussion counts
      - list of pending expert requests (name, institution, disciplines)
    All computed in 4 DB queries — safe to call on every dashboard mount.
    """
    permission_classes = (IsAdmin,)

    def get(self, request):
        from apps.heritage.models import HeritageResource  # avoid circular import
        from apps.discussions.models import Discussion

        total_users = User.objects.count()
        pending_users = User.objects.filter(status=User.Status.PENDING).count()
        active_users = User.objects.filter(status=User.Status.ACTIVE).count()

        total_projects = HeritageResource.objects.count()
        open_conflicts = Discussion.objects.filter(status=Discussion.Status.OPEN).count()

        pending_experts = User.objects.filter(
            status=User.Status.PENDING
        ).prefetch_related("disciplines").order_by("created_at")[:10]

        experts_data = [
            {
                "id": u.id,
                "full_name": f"{u.first_name} {u.last_name}".strip() or u.email,
                "email": u.email,
                "institution": u.institution_name or "",
                "disciplines": [d.name_fr for d in u.disciplines.all()],
                "created_at": u.created_at.isoformat(),
            }
            for u in pending_experts
        ]

        return Response({
            "total_users": total_users,
            "pending_users": pending_users,
            "active_users": active_users,
            "total_projects": total_projects,
            "open_conflicts": open_conflicts,
            "pending_experts": experts_data,
        })
