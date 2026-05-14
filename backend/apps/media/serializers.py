import os

from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import Annotation, Media

# 3D model whitelist — GLB is the universal cross-platform format,
# GLTF is its JSON-text counterpart. We accept both extensions and the
# canonical mime types. Browsers often report empty/octet-stream for GLB,
# so extension is authoritative.
GLB_EXTENSIONS = (".glb", ".gltf")
GLB_MIME_TYPES = ("model/gltf-binary", "model/gltf+json")
MAX_MODEL_3D_BYTES = 50 * 1024 * 1024  # 50 MB


class MediaSerializer(serializers.ModelSerializer):
    uploader = UserMiniSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = (
            "id", "project", "uploader",
            "media_type", "file", "file_url",
            "mime_type", "size_bytes",
            "width", "height", "duration_seconds",
            "thumbnail", "thumbnail_url",
            "caption", "license",
            "longitude", "latitude",
            "ai_tags", "ai_status",
            "created_at",
        )
        read_only_fields = (
            "uploader", "mime_type", "size_bytes",
            "width", "height", "duration_seconds",
            "thumbnail", "ai_tags", "ai_status", "created_at",
        )

    def get_file_url(self, obj):
        request = self.context.get("request")
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return obj.file.url if obj.file else None

    def get_thumbnail_url(self, obj):
        request = self.context.get("request")
        if obj.thumbnail and request:
            return request.build_absolute_uri(obj.thumbnail.url)
        return obj.thumbnail.url if obj.thumbnail else None

    def get_longitude(self, obj):
        return obj.geo_point.x if obj.geo_point else None

    def get_latitude(self, obj):
        return obj.geo_point.y if obj.geo_point else None


class MediaUploadSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(required=False, write_only=True)
    latitude = serializers.FloatField(required=False, write_only=True)

    class Meta:
        model = Media
        fields = (
            "id", "project", "media_type", "file",
            "caption", "license",
            "longitude", "latitude",
        )

    def validate(self, attrs):
        media_type = attrs.get("media_type")
        f = attrs.get("file")
        if media_type == Media.Type.MODEL_3D and f is not None:
            ext = os.path.splitext(getattr(f, "name", "") or "")[1].lower()
            mime = (getattr(f, "content_type", "") or "").lower()
            if ext not in GLB_EXTENSIONS and mime not in GLB_MIME_TYPES:
                raise serializers.ValidationError({
                    "file": "Only .glb or .gltf 3D models are accepted.",
                })
            size = getattr(f, "size", 0) or 0
            if size > MAX_MODEL_3D_BYTES:
                raise serializers.ValidationError({
                    "file": f"3D model exceeds {MAX_MODEL_3D_BYTES // (1024 * 1024)} MB limit.",
                })
        return attrs

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lng = validated_data.pop("longitude", None)
        lat = validated_data.pop("latitude", None)

        f = validated_data.get("file")
        if f is not None:
            validated_data["mime_type"] = getattr(f, "content_type", "") or ""
            validated_data["size_bytes"] = getattr(f, "size", 0) or 0

        if lng is not None and lat is not None:
            validated_data["geo_point"] = Point(lng, lat, srid=4326)

        return super().create(validated_data)


class AnnotationSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = Annotation
        fields = (
            "id", "media", "resource",
            "geometry_json",
            "longitude", "latitude",
            "body_text",
            "author", "discipline",
            "is_ai_generated", "is_validated", "validated_by",
            "created_at",
        )
        read_only_fields = ("author", "validated_by", "created_at")

    def get_longitude(self, obj):
        return obj.geo_point.x if obj.geo_point else None

    def get_latitude(self, obj):
        return obj.geo_point.y if obj.geo_point else None


class AnnotationWriteSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(required=False, write_only=True)
    latitude = serializers.FloatField(required=False, write_only=True)

    class Meta:
        model = Annotation
        fields = (
            "id", "media", "resource",
            "geometry_json",
            "longitude", "latitude",
            "body_text", "discipline",
            "is_ai_generated",
        )

    def validate(self, attrs):
        media = attrs.get("media")
        resource = attrs.get("resource")
        if not media and not resource:
            raise serializers.ValidationError("Provide either `media` or `resource`.")
        if media and resource:
            raise serializers.ValidationError("Provide only one of `media` or `resource`.")
        return attrs

    def create(self, validated_data):
        from django.contrib.gis.geos import Point

        lng = validated_data.pop("longitude", None)
        lat = validated_data.pop("latitude", None)

        if lng is not None and lat is not None:
            validated_data["geo_point"] = Point(lng, lat, srid=4326)

        # AI-generated annotations require validation
        if validated_data.get("is_ai_generated"):
            validated_data["is_validated"] = False

        return super().create(validated_data)
