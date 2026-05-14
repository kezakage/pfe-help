"""Project visibility & publish action."""
import pytest

pytestmark = pytest.mark.django_db


def test_anonymous_only_sees_published_projects(api_client, project_published, project_draft):
    res = api_client.get("/api/v1/heritage/projects/")
    assert res.status_code == 200
    body = res.json()
    items = body if isinstance(body, list) else body.get("results", [])
    titles = {p["title"] for p in items}
    assert "Projet publié" in titles
    assert "Projet brouillon" not in titles


def test_admin_sees_all_projects(auth_client, admin_user, project_published, project_draft):
    client = auth_client(admin_user)
    res = client.get("/api/v1/heritage/projects/")
    assert res.status_code == 200
    body = res.json()
    items = body if isinstance(body, list) else body.get("results", [])
    titles = {p["title"] for p in items}
    assert {"Projet publié", "Projet brouillon"} <= titles


def test_member_sees_their_draft_project(auth_client, expert_user, project_draft):
    """The expert created the draft & is its lead — they must see it."""
    client = auth_client(expert_user)
    res = client.get("/api/v1/heritage/projects/")
    assert res.status_code == 200
    body = res.json()
    items = body if isinstance(body, list) else body.get("results", [])
    assert any(p["title"] == "Projet brouillon" for p in items)


def test_publish_action_changes_status(auth_client, expert_user, project_draft):
    client = auth_client(expert_user)
    res = client.post(f"/api/v1/heritage/projects/{project_draft.id}/publish/")
    assert res.status_code == 200, res.content
    assert res.json()["status"] == "published"
    project_draft.refresh_from_db()
    assert project_draft.status == "published"
