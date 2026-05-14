from rest_framework import permissions, viewsets

from .models import ExportJob
from .serializers import ExportJobSerializer


class ExportJobViewSet(viewsets.ModelViewSet):
    queryset = ExportJob.objects.select_related("requested_by", "project").all()
    serializer_class = ExportJobSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["status", "format", "project"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        if user.is_staff or getattr(user, "role", "") == "admin":
            return qs
        return qs.filter(requested_by=user)

    def perform_create(self, serializer):
        job = serializer.save(requested_by=self.request.user)
        try:
            from .tasks import run_export_job
            run_export_job.delay(job.id)
        except Exception:
            # If broker unavailable, leave job pending; an operator can retry.
            pass
