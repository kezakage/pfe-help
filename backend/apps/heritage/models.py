"""
Heritage resources and collaborative projects.

Schema (simplified, per project context):
  - HeritageResource (geo_point via PostGIS)
  - Project (1 ↔ 1 with HeritageResource)
  - ProjectMember (M2M with role per project)
"""
from django.conf import settings
from django.contrib.gis.db import models as gis_models
from django.db import models
from django.utils.translation import gettext_lazy as _


class HeritageResource(models.Model):
    class Period(models.TextChoices):
        PREHISTORIC = "prehistoric", _("Prehistoric")
        NUMIDIAN = "numidian", _("Numidian")
        ROMAN = "roman", _("Roman")
        MEDIEVAL = "medieval", _("Medieval")
        OTTOMAN = "ottoman", _("Ottoman")
        COLONIAL = "colonial", _("Colonial")
        CONTEMPORARY = "contemporary", _("Contemporary")

    class ArchitecturalType(models.TextChoices):
        MOSQUE = "mosque", _("Mosque")
        MEDERSA = "medersa", _("Medersa")
        CASBAH = "casbah", _("Casbah / Medina")
        PALACE = "palace", _("Palace")
        FORTIFICATION = "fortification", _("Fortification")
        CHURCH = "church", _("Church")
        SYNAGOGUE = "synagogue", _("Synagogue")
        MAUSOLEUM = "mausoleum", _("Mausoleum")
        TRADITIONAL_HOUSE = "traditional_house", _("Traditional house")
        ARCHAEOLOGICAL_SITE = "archaeological_site", _("Archaeological site")
        OTHER = "other", _("Other")

    class ClassificationLevel(models.TextChoices):
        UNESCO = "unesco", _("UNESCO World Heritage")
        NATIONAL = "national", _("National")
        REGIONAL = "regional", _("Regional")
        UNCLASSIFIED = "unclassified", _("Unclassified")

    name_fr = models.CharField(max_length=200)
    name_ar = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)

    period = models.CharField(max_length=20, choices=Period.choices, db_index=True)
    architectural_type = models.CharField(max_length=24, choices=ArchitecturalType.choices, db_index=True)

    wilaya = models.CharField(max_length=80, db_index=True)
    commune = models.CharField(max_length=80, blank=True)
    address = models.CharField(max_length=255, blank=True)

    # PostGIS POINT (longitude, latitude)
    geo_point = gis_models.PointField(geography=True, null=True, blank=True)

    classification_level = models.CharField(
        max_length=14, choices=ClassificationLevel.choices,
        default=ClassificationLevel.UNCLASSIFIED, db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name_fr",)
        indexes = [
            models.Index(fields=["period", "architectural_type"]),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return self.name_fr


class Project(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        IN_PROGRESS = "in_progress", _("In progress")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    resource = models.OneToOneField(
        HeritageResource, on_delete=models.PROTECT, related_name="project"
    )
    title = models.CharField(max_length=240)
    description = models.TextField(blank=True)
    status = models.CharField(
        max_length=14, choices=Status.choices, default=Status.DRAFT, db_index=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_projects"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ProjectMember",
        related_name="projects",
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        indexes = [models.Index(fields=["status", "updated_at"])]

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class ProjectMember(models.Model):
    """Membership with a per-project role."""

    class ProjectRole(models.TextChoices):
        LEAD = "lead", _("Project lead")
        CONTRIBUTOR = "contributor", _("Contributor")
        REVIEWER = "reviewer", _("Reviewer")

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project_role = models.CharField(max_length=14, choices=ProjectRole.choices, default=ProjectRole.CONTRIBUTOR)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("project", "user")
        ordering = ("joined_at",)
