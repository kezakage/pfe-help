from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.accounts.models import User

from .models import Project, ProjectMember


class IsProjectMemberOrReadOnlyPublic(BasePermission):
    """
    - Read access: published projects are public; non-published require membership.
    - Write access: only members (or admins).
    """

    def has_object_permission(self, request, view, obj: Project) -> bool:
        u = request.user
        if request.method in SAFE_METHODS:
            if obj.status == Project.Status.PUBLISHED:
                return True
            if not (u and u.is_authenticated):
                return False
            if u.role == User.Role.ADMIN:
                return True
            return ProjectMember.objects.filter(project=obj, user=u).exists()

        # write
        if not (u and u.is_authenticated):
            return False
        if u.role == User.Role.ADMIN:
            return True
        return ProjectMember.objects.filter(project=obj, user=u).exists()


def user_is_project_lead(user, project: Project) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.role == User.Role.ADMIN:
        return True
    return ProjectMember.objects.filter(
        project=project, user=user, project_role=ProjectMember.ProjectRole.LEAD
    ).exists()
