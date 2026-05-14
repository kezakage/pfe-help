from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import ExportJob


class ExportJobSerializer(serializers.ModelSerializer):
    requested_by = UserMiniSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ExportJob
        fields = (
            "id", "requested_by", "project",
            "format", "status", "options",
            "file", "file_url", "error_message",
            "created_at", "started_at", "finished_at",
        )
        read_only_fields = (
            "requested_by", "status", "file", "error_message",
            "started_at", "finished_at", "created_at",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None
