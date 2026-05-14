"""Authentication & profile endpoints."""
import pytest

pytestmark = pytest.mark.django_db


def test_login_returns_access_and_refresh_tokens(api_client, expert_user):
    expert_user.set_password("Secret123!")
    expert_user.save()
    res = api_client.post(
        "/api/v1/auth/login/",
        {"email": "expert@test.dz", "password": "Secret123!"},
        format="json",
    )
    assert res.status_code == 200, res.content
    body = res.json()
    assert "access" in body and "refresh" in body
    # The login response should expose the user payload (used by the frontend)
    assert body.get("user", {}).get("email") == "expert@test.dz"


def test_login_with_wrong_password_fails(api_client, expert_user):
    expert_user.set_password("right")
    expert_user.save()
    res = api_client.post(
        "/api/v1/auth/login/",
        {"email": "expert@test.dz", "password": "wrong"},
        format="json",
    )
    assert res.status_code == 401


def test_me_endpoint_requires_auth(api_client):
    res = api_client.get("/api/v1/auth/me/")
    assert res.status_code in (401, 403)


def test_me_endpoint_returns_current_user(auth_client, expert_user):
    client = auth_client(expert_user)
    res = client.get("/api/v1/auth/me/")
    assert res.status_code == 200, res.content
    # MeViewSet usually returns a list-shape; accept either dict or list
    data = res.json()
    payload = data[0] if isinstance(data, list) and data else data
    if isinstance(payload, dict) and "results" in payload:
        payload = payload["results"][0]
    assert payload["email"] == "expert@test.dz"
