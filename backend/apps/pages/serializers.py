from rest_framework import serializers

from apps.accounts.serializers import DisciplineSerializer, UserMiniSerializer

from .models import Page, PageVersion


class PageVersionMiniSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    discipline = DisciplineSerializer(read_only=True)

    class Meta:
        model = PageVersion
        fields = ("id", "version_number", "change_summary", "author",
                  "discipline", "status", "created_at", "parent_version")
        read_only_fields = fields


class PageVersionSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    discipline = DisciplineSerializer(read_only=True)
    discipline_id = serializers.PrimaryKeyRelatedField(
        queryset=DisciplineSerializer.Meta.model.objects.all(),
        source="discipline", write_only=True, required=False, allow_null=True,
    )

    class Meta:
        model = PageVersion
        fields = (
            "id", "page", "version_number", "parent_version",
            "content_json", "change_summary",
            "author", "discipline", "discipline_id",
            "status", "created_at",
        )
        read_only_fields = ("version_number", "author", "created_at", "page")


class PageSerializer(serializers.ModelSerializer):
    current_version = PageVersionMiniSerializer(read_only=True)
    versions_count = serializers.IntegerField(source="versions.count", read_only=True)

    class Meta:
        model = Page
        fields = (
            "id", "project", "title", "position",
            "current_version", "versions_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "current_version", "versions_count")
