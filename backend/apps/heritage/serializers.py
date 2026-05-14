from rest_framework import serializers

from apps.accounts.serializers import UserMiniSerializer

from .models import HeritageResource, Project, ProjectMember


class HeritageResourceSerializer(serializers.ModelSerializer):
    longitude = serializers.SerializerMethodField()
    latitude = serializers.SerializerMethodField()

    class Meta:
        model = HeritageResource
        fields = (
            "id", "name_fr", "name_ar", "description",
            "period", "architectural_type",
            "wilaya", "commune", "address",
            "longitude", "latitude",
            "classification_level",
            "created_at", "updated_at",
        )

    def get_longitude(self, obj):
        return obj.geo_point.x if obj.geo_point else None

    def get_latitude(self, obj):
        return obj.geo_point.y if obj.geo_point else None


class HeritageResourceWriteSerializer(serializers.ModelSerializer):
    longitude = serializers.FloatField(write_only=True, required=False)
    latitude = serializers.FloatField(write_only=True, required=False)

    class Meta:
        model = HeritageResource
        fields = (
            "id", "name_fr", "name_ar", "description",
            "period", "architectural_type",
            "wilaya", "commune", "address",
            "longitude", "latitude",
            "classification_level",
        )

    def _set_point(self, instance, validated):
        from django.contrib.gis.geos import Point
        lng = validated.pop("longitude", None)
        lat = validated.pop("latitude", None)
        if lng is not None and lat is not None:
            instance.geo_point = Point(float(lng), float(lat))

    def create(self, validated_data):
        instance = HeritageResource(**{k: v for k, v in validated_data.items()
                                       if k not in ("longitude", "latitude")})
        self._set_point(instance, validated_data)
        instance.save()
        return instance

    def update(self, instance, validated_data):
        self._set_point(instance, validated_data)
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        return instance


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = UserMiniSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = ProjectMember
        fields = ("id", "user", "user_id", "project_role", "joined_at")
        read_only_fields = ("joined_at",)


class ProjectSerializer(serializers.ModelSerializer):
    resource = HeritageResourceSerializer(read_only=True)
    resource_id = serializers.PrimaryKeyRelatedField(
        queryset=HeritageResource.objects.all(), source="resource", write_only=True
    )
    created_by = UserMiniSerializer(read_only=True)
    member_count = serializers.IntegerField(source="memberships.count", read_only=True)

    class Meta:
        model = Project
        fields = (
            "id", "title", "description", "status",
            "resource", "resource_id",
            "created_by", "member_count",
            "created_at", "updated_at",
        )
        read_only_fields = ("created_at", "updated_at", "created_by", "member_count")
