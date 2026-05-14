"""
Accounts — User and Discipline.
Implements the simplified schema:
  - USER (single role field, status for admin validation)
  - DISCIPLINE (referential)
  - USER_DISCIPLINE (M2M association)
"""
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Manager using email as the unique identifier."""

    use_in_migrations = True

    def _create_user(self, email: str, password: str | None, **extra_fields):
        if not email:
            raise ValueError(_("The email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None = None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("status", User.Status.ACTIVE)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self._create_user(email, password, **extra_fields)


class Discipline(models.Model):
    """Reference table for disciplines (architecture, history, archaeology...)."""

    name_fr = models.CharField(max_length=80, unique=True)
    name_ar = models.CharField(max_length=80, blank=True)
    color_hex = models.CharField(
        max_length=7, default="#824c2b",
        help_text="Used for contributor color-coding in the rich editor.",
    )

    class Meta:
        ordering = ("name_fr",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name_fr


class User(AbstractUser):
    """
    Custom user implementing the simplified schema.

    `username` is removed in favor of `email`.
    A single `role` field handles RBAC; finer permissions go through Guardian
    on a per-object basis (e.g. ProjectMember).
    """

    class Role(models.TextChoices):
        ADMIN = "admin", _("Administrator")
        EXPERT = "expert", _("Validated expert")
        RESEARCHER = "researcher", _("Guest researcher")
        VISITOR = "visitor", _("Visitor")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending validation")
        ACTIVE = "active", _("Active")
        REJECTED = "rejected", _("Rejected")

    username = None
    email = models.EmailField(_("email address"), unique=True, db_index=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=80, blank=True)

    role = models.CharField(
        max_length=12, choices=Role.choices, default=Role.RESEARCHER
    )
    status = models.CharField(
        max_length=12, choices=Status.choices, default=Status.PENDING
    )

    bio = models.TextField(blank=True)
    institution_name = models.CharField(max_length=160, blank=True)

    disciplines = models.ManyToManyField(
        Discipline, through="UserDiscipline", related_name="users", blank=True
    )

    validated_by = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL,
        related_name="validated_users",
        limit_choices_to={"role": "admin"},
    )
    validated_at = models.DateTimeField(null=True, blank=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["role", "status"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email

    @property
    def is_validated_expert(self) -> bool:
        return self.role == self.Role.EXPERT and self.status == self.Status.ACTIVE


class UserDiscipline(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    is_primary = models.BooleanField(default=False)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "discipline")
