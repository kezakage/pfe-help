from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import User


class IsAdmin(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.role == User.Role.ADMIN)


class IsValidatedExpert(BasePermission):
    def has_permission(self, request, view) -> bool:
        u = request.user
        return bool(u and u.is_authenticated and u.is_validated_expert)


class IsExpertOrReadOnly(BasePermission):
    """
    Read access for everyone (including anonymous visitors of the public
    catalogue); write access reserved to validated experts and admins.
    """

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        u = request.user
        if not (u and u.is_authenticated):
            return False
        return u.role == User.Role.ADMIN or u.is_validated_expert


class IsSelfOrAdmin(BasePermission):
    """Object-level: object must be the requesting user, or requester is admin."""

    def has_object_permission(self, request, view, obj) -> bool:
        u = request.user
        if not (u and u.is_authenticated):
            return False
        if u.role == User.Role.ADMIN:
            return True
        return obj == u
