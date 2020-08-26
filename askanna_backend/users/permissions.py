from rest_framework import permissions
from users.models import Membership


def _is_in_group(user, role):
    """
    Takes a user and a role name, and returns `True` if the user is in that group.
    """
    try:
        return Membership.objects.get(role=role).user_set.filter(user=user.user).exists()
    except Membership.DoesNotExist:
        return None


def _has_group_permission(user, required_roles):
    return any([_is_in_group(user, role) for role in required_roles])


class IsAdminUser(permissions.BasePermission):
    required_roles = ['Admin']

    def has_permission(self, request, view):
        has_group_permission = _has_group_permission(request.user, self.required_roles)
        return request.user and has_group_permission

    def has_object_permission(self, request, view, obj):
        has_group_permission = _has_group_permission(request.user, self.required_roles)
        return request.user and has_group_permission


class IsMemberOrAdminUser(permissions.BasePermission):
    required_roles = ['Admin', 'Member']

    def has_object_permission(self, request, view, obj):
        has_group_permission = _has_group_permission(request.user, self.required_roles)
        return request.user and has_group_permission

