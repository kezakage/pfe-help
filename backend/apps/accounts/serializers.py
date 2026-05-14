from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Discipline, User, UserDiscipline


class DisciplineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ("id", "name_fr", "name_ar", "color_hex")


class UserMiniSerializer(serializers.ModelSerializer):
    """Minimal user representation, embedded in many resources."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "role", "status")
        read_only_fields = fields


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    disciplines = DisciplineSerializer(many=True, read_only=True)
    discipline_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, required=False,
        queryset=Discipline.objects.all(), source="disciplines",
    )

    class Meta:
        model = User
        fields = (
            "id", "email", "first_name", "last_name", "full_name",
            "role", "status", "bio", "institution_name",
            "disciplines", "discipline_ids",
            "validated_at", "created_at", "last_login_at",
        )
        read_only_fields = ("role", "status", "validated_at", "created_at", "last_login_at")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    discipline_ids = serializers.PrimaryKeyRelatedField(
        many=True, write_only=True, required=False,
        queryset=Discipline.objects.all(),
    )
    requested_role = serializers.ChoiceField(
        choices=[User.Role.RESEARCHER, User.Role.EXPERT],
        default=User.Role.RESEARCHER,
        write_only=True,
    )

    class Meta:
        model = User
        fields = (
            "email", "password", "first_name", "last_name",
            "institution_name", "bio", "discipline_ids", "requested_role",
        )

    def create(self, validated_data):
        disciplines = validated_data.pop("discipline_ids", [])
        requested = validated_data.pop("requested_role")
        user = User.objects.create_user(
            **validated_data,
            role=requested,
            # experts always start as PENDING; researchers can be ACTIVE directly
            status=User.Status.PENDING if requested == User.Role.EXPERT else User.Status.ACTIVE,
        )
        for d in disciplines:
            UserDiscipline.objects.create(user=user, discipline=d)
        return user


class TokenSerializer(TokenObtainPairSerializer):
    """Embed user info in the JWT response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["status"] = user.status
        token["email"] = user.email
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserMiniSerializer(self.user).data
        return data


class ValidateExpertSerializer(serializers.Serializer):
    decision = serializers.ChoiceField(choices=[("approve", "approve"), ("reject", "reject")])
    note = serializers.CharField(required=False, allow_blank=True)
