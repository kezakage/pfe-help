"""
Tests for the OAuth2 / SSO endpoints.

We stub out the actual provider HTTP calls so the suite never hits Google
or GitHub. Coverage:
  * /auth/social/providers/ reflects whether credentials are configured
  * /auth/social/<provider>/ → 503 when the provider isn't configured
  * SocialAccountAdapter.populate_user marks fresh SSO users as ACTIVE
  * pre_social_login auto-links to a pre-existing user via email
"""
from unittest.mock import MagicMock

import pytest
from django.test import override_settings

from apps.accounts.allauth_adapters import SocialAccountAdapter
from apps.accounts.models import User

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# /auth/social/providers/
# ---------------------------------------------------------------------------
def test_providers_status_reflects_disabled_state(api_client):
    """No credentials in env → both providers reported as disabled."""
    res = api_client.get("/api/v1/auth/social/providers/")
    assert res.status_code == 200
    body = res.json()
    assert body["google"]["enabled"] is False
    assert body["github"]["enabled"] is False
    assert body["google"]["authorize_url"] == "https://accounts.google.com/o/oauth2/v2/auth"
    assert body["github"]["authorize_url"] == "https://github.com/login/oauth/authorize"


@override_settings(SOCIALACCOUNT_PROVIDERS={
    "google": {"APP": {"client_id": "fake-id", "secret": "x", "key": ""},
               "SCOPE": ["profile", "email"]},
    "github": {"APP": {"client_id": "", "secret": "", "key": ""}, "SCOPE": []},
})
def test_providers_status_reflects_enabled_state(api_client):
    """When client_id is set, the provider shows up as enabled."""
    res = api_client.get("/api/v1/auth/social/providers/")
    assert res.status_code == 200
    body = res.json()
    assert body["google"]["enabled"] is True
    assert body["google"]["client_id"] == "fake-id"
    assert body["github"]["enabled"] is False


# ---------------------------------------------------------------------------
# /auth/social/google/ + /auth/social/github/
# ---------------------------------------------------------------------------
def test_google_login_returns_503_when_not_configured(api_client):
    res = api_client.post(
        "/api/v1/auth/social/google/",
        {"code": "abc", "redirect_uri": "http://localhost:5173/auth/google/callback"},
        format="json",
    )
    assert res.status_code == 503
    body = res.json()
    assert body["error"] == "provider_not_configured"
    assert body["provider"] == "google"


def test_github_login_returns_503_when_not_configured(api_client):
    res = api_client.post(
        "/api/v1/auth/social/github/",
        {"code": "abc", "redirect_uri": "http://localhost:5173/auth/github/callback"},
        format="json",
    )
    assert res.status_code == 503
    assert res.json()["provider"] == "github"


# ---------------------------------------------------------------------------
# SocialAccountAdapter — business rules around new SSO users
# ---------------------------------------------------------------------------
def test_populate_user_marks_sso_account_as_active():
    """Fresh SSO sign-ups bypass the admin-validation queue."""
    adapter = SocialAccountAdapter()
    sociallogin = MagicMock()
    sociallogin.user = User(email="newbie@example.com")
    user = adapter.populate_user(
        request=None,
        sociallogin=sociallogin,
        data={"email": "newbie@example.com", "name": "Amina Belhadj"},
    )
    assert user.status == User.Status.ACTIVE
    assert user.role == User.Role.RESEARCHER
    # Name split from the provider's `name` field
    assert user.first_name == "Amina"
    assert user.last_name == "Belhadj"


def test_populate_user_with_single_name_part():
    adapter = SocialAccountAdapter()
    sociallogin = MagicMock()
    sociallogin.user = User(email="solo@example.com")
    user = adapter.populate_user(
        request=None, sociallogin=sociallogin,
        data={"email": "solo@example.com", "name": "Yassine"},
    )
    assert user.first_name == "Yassine"
    assert user.last_name == ""


def test_pre_social_login_links_to_existing_user_by_email():
    """A user who originally signed up via password/email should be reused
    when they later log in through Google with the same email."""
    existing = User.objects.create_user(
        email="amina@univ.dz", password="x", first_name="Amina"
    )
    adapter = SocialAccountAdapter()
    sociallogin = MagicMock()
    sociallogin.is_existing = False
    sociallogin.user = MagicMock(email="Amina@univ.dz")  # case-insensitive match
    adapter.pre_social_login(request=None, sociallogin=sociallogin)
    sociallogin.connect.assert_called_once()
    # Second positional arg of connect() is the resolved User instance.
    connected_user = sociallogin.connect.call_args.args[1]
    assert connected_user.id == existing.id


def test_pre_social_login_no_match_does_not_connect():
    adapter = SocialAccountAdapter()
    sociallogin = MagicMock()
    sociallogin.is_existing = False
    sociallogin.user = MagicMock(email="ghost@example.com")
    adapter.pre_social_login(request=None, sociallogin=sociallogin)
    sociallogin.connect.assert_not_called()
