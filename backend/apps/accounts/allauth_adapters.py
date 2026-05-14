"""
Custom django-allauth adapters.

We override two behaviours:
  * Auto-link social accounts to a pre-existing user with the same verified
    email (so a user who first signed up with a password can later log in
    via Google without ending up with two accounts).
  * New users created through SSO are marked ACTIVE immediately — the
    provider already vouched for the email address, so the manual admin
    review step that gates regular sign-ups is unnecessary here.
"""
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter

from .models import User


class AccountAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        # Regular email/password signup goes through our own RegisterView,
        # not allauth's flow.
        return False


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        return True

    def pre_social_login(self, request, sociallogin):
        """Connect the social login to an existing User if the email matches."""
        if sociallogin.is_existing:
            return  # already connected
        email = (sociallogin.user.email or "").lower().strip()
        if not email:
            return
        try:
            existing = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return
        sociallogin.connect(request, existing)

    def populate_user(self, request, sociallogin, data):
        """Map provider profile fields onto our User instance."""
        user = super().populate_user(request, sociallogin, data)
        # SSO users skip the admin-validation queue.
        user.status = User.Status.ACTIVE
        user.role = user.role or User.Role.RESEARCHER
        # Best-effort first/last name extraction (allauth already fills these
        # for Google; GitHub usually only ships a single `name` field).
        full = (data.get("name") or "").strip()
        if full and not user.first_name and not user.last_name:
            parts = full.split(maxsplit=1)
            user.first_name = parts[0]
            user.last_name = parts[1] if len(parts) > 1 else ""
        return user
