"""
Project-wide pytest fixtures.

These fixtures provide:
  - api_client: anonymous DRF APIClient
  - admin_user / expert_user / researcher_user / pending_user: pre-built users
  - auth_client(user): factory returning a DRF client with JWT for that user
  - resource_unesco / resource_national: minimal HeritageResource fixtures
  - project_published / project_draft: minimal Project fixtures
"""
import pytest
from django.contrib.gis.geos import Point
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.heritage.models import HeritageResource, Project, ProjectMember


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------
@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client():
    """Return a factory: auth_client(user) -> APIClient with Bearer JWT."""
    def _make(user):
        client = APIClient()
        token = RefreshToken.for_user(user).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client
    return _make


# ---------------------------------------------------------------------------
# Users (one per role; status = active unless name says otherwise)
# ---------------------------------------------------------------------------
@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@test.dz", password="x",
        first_name="A", last_name="Admin",
        role=User.Role.ADMIN, status=User.Status.ACTIVE,
        is_staff=True, is_superuser=True,
    )


@pytest.fixture
def expert_user(db):
    return User.objects.create_user(
        email="expert@test.dz", password="x",
        first_name="E", last_name="Expert",
        role=User.Role.EXPERT, status=User.Status.ACTIVE,
    )


@pytest.fixture
def researcher_user(db):
    return User.objects.create_user(
        email="researcher@test.dz", password="x",
        first_name="R", last_name="Researcher",
        role=User.Role.RESEARCHER, status=User.Status.ACTIVE,
    )


@pytest.fixture
def pending_expert(db):
    """Expert role but pending validation — should NOT be able to write."""
    return User.objects.create_user(
        email="pending@test.dz", password="x",
        first_name="P", last_name="Pending",
        role=User.Role.EXPERT, status=User.Status.PENDING,
    )


# ---------------------------------------------------------------------------
# Heritage resources & projects
# ---------------------------------------------------------------------------
@pytest.fixture
def resource_unesco(db):
    return HeritageResource.objects.create(
        name_fr="Casbah de test", name_ar="قصبة الاختبار",
        description="Fixture UNESCO",
        period=HeritageResource.Period.OTTOMAN,
        architectural_type=HeritageResource.ArchitecturalType.CASBAH,
        wilaya="Alger", commune="Casbah",
        geo_point=Point(3.0588, 36.7833, srid=4326),
        classification_level=HeritageResource.ClassificationLevel.UNESCO,
    )


@pytest.fixture
def resource_national(db):
    return HeritageResource.objects.create(
        name_fr="Mosquée de test",
        period=HeritageResource.Period.MEDIEVAL,
        architectural_type=HeritageResource.ArchitecturalType.MOSQUE,
        wilaya="Tlemcen", commune="Tlemcen",
        geo_point=Point(-1.317, 34.883, srid=4326),
        classification_level=HeritageResource.ClassificationLevel.NATIONAL,
    )


@pytest.fixture
def project_published(db, expert_user, resource_unesco):
    p = Project.objects.create(
        resource=resource_unesco,
        title="Projet publié",
        status=Project.Status.PUBLISHED,
        created_by=expert_user,
    )
    ProjectMember.objects.create(
        project=p, user=expert_user,
        project_role=ProjectMember.ProjectRole.LEAD,
    )
    return p


@pytest.fixture
def project_draft(db, expert_user, resource_national):
    p = Project.objects.create(
        resource=resource_national,
        title="Projet brouillon",
        status=Project.Status.DRAFT,
        created_by=expert_user,
    )
    ProjectMember.objects.create(
        project=p, user=expert_user,
        project_role=ProjectMember.ProjectRole.LEAD,
    )
    return p
