"""
Social login endpoints — bridge OAuth2 providers to our SimpleJWT pair.

Flow (authorization-code, server-to-server token exchange):
  1. Frontend redirects user to provider's authorize URL with our client_id,
     scope, and redirect_uri pointing back to a frontend route.
  2. Provider sends the user back to that frontend route with `?code=...`.
  3. Frontend POSTs `{code, redirect_uri}` to /api/v1/auth/social/<provider>/.
  4. We hand the code to dj-rest-auth's SocialLoginView, which uses allauth's
     adapters to swap it for an access token, fetch the profile, and either
     create or look up the User. Our SocialAccountAdapter pre-links by email
     and forces status=ACTIVE for fresh SSO sign-ups.
  5. Response: SimpleJWT access + refresh + user payload.
"""
from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from django.conf import settings
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView


class _ConfiguredSocialLoginView(SocialLoginView):
    """
    Wraps SocialLoginView with a soft-fail when the provider has no credentials.
    This keeps the API up in dev environments where SSO isn't configured yet.
    """
    permission_classes = (permissions.AllowAny,)
    client_class = OAuth2Client
    provider_id: str = ""  # set by subclasses; matches keys in SOCIALACCOUNT_PROVIDERS

    def post(self, request, *args, **kwargs):
        cfg = settings.SOCIALACCOUNT_PROVIDERS.get(self.provider_id, {})
        if not cfg.get("APP", {}).get("client_id"):
            return Response(
                {"error": "provider_not_configured", "provider": self.provider_id},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return super().post(request, *args, **kwargs)


class GoogleLoginView(_ConfiguredSocialLoginView):
    provider_id = "google"
    adapter_class = GoogleOAuth2Adapter
    callback_url = settings.SOCIAL_REDIRECT_FRONTEND + "/auth/google/callback"


class GitHubLoginView(_ConfiguredSocialLoginView):
    provider_id = "github"
    adapter_class = GitHubOAuth2Adapter
    callback_url = settings.SOCIAL_REDIRECT_FRONTEND + "/auth/github/callback"


class SocialProvidersStatusView(APIView):
    """
    GET /api/v1/auth/social/providers/ — tells the frontend which provider
    buttons to show (only those that actually have credentials).
    """
    permission_classes = (permissions.AllowAny,)

    def get(self, request):
        cfg = settings.SOCIALACCOUNT_PROVIDERS
        return Response({
            "google": {
                "enabled": bool(cfg.get("google", {}).get("APP", {}).get("client_id")),
                "client_id": cfg.get("google", {}).get("APP", {}).get("client_id", ""),
                "scope": cfg.get("google", {}).get("SCOPE", []),
                "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
                "callback_path": "/auth/google/callback",
            },
            "github": {
                "enabled": bool(cfg.get("github", {}).get("APP", {}).get("client_id")),
                "client_id": cfg.get("github", {}).get("APP", {}).get("client_id", ""),
                "scope": cfg.get("github", {}).get("SCOPE", []),
                "authorize_url": "https://github.com/login/oauth/authorize",
                "callback_path": "/auth/github/callback",
            },
        })
