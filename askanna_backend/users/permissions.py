from rest_framework import permissions
from users.models import Membership, WS_ADMIN, WS_MEMBER
from django.db.models import Q
import rest_framework

class IsAdminUser(permissions.BasePermission):
    """
    In this permission check we assume that the instance model contains
    the fields:

    - role
    - user

    """

    required_roles = [WS_ADMIN]

    def has_permission(self, request, view):
        # is this user part of the queryset in the view?
        # in other words, is this user part of the Model
        members = view.get_queryset()
        return (
            members.filter(user=request.user, role__in=self.required_roles).exists()
        )

    def has_object_permission(self, request, view, obj):

        # can the user modify the object (row based access)
        # is the user an admin
        # specific rules to modify specific fields can be defined later in serializer
        # this permission only checks access
        members = view.get_queryset()
        is_admin = members.filter(user=request.user, role=WS_ADMIN).exists()

        return obj.user == request.user or is_admin


class IsMemberOrAdminUser(permissions.BasePermission):
    required_roles = [WS_ADMIN, WS_MEMBER]

    def has_permission(self, request, view):
        # is this user part of the queryset in the view?
        # in other words, is this user part of the Model
        members = view.get_queryset()
        return (
            members.filter(user=request.user, role__in=self.required_roles).exists()
        )

    def has_object_permission(self, request, view, obj):

        # can the user modify the object (row based access)
        # is owner or is admin
        # specific rules to modify specific fields can be defined later in serializer
        # this permission only checks access
        members = view.get_queryset()
        is_admin = members.filter(user=request.user, role=WS_ADMIN).exists()

        return obj.user == request.user or is_admin


class RoleUpdateByAdminOnlyPermission(permissions.BasePermission):
    """
    This permission class is to make sure that the role can only be changed by admin users of the workspace
    Admin users can only upgrade member users, downgrade admin users is not possible.
    """
    def has_permission(self, request, view):
        if "role" in request.data:
            if request.data["role"] == "WA":
                parents = view.get_parents_query_dict()
                user = request.user
                return user.memberships.filter(**parents, role=WS_ADMIN).exists()
            elif request.data["role"] == "WM":
                return False

        return True


class RequestHasAccessToWorkspacePermission(permissions.BasePermission):
    """
    This permission class is to make sure that the user is a member of the workspace
    """
    def has_permission(self, request, view):
        """
        If an anonymous user wants to retrieve it needs a valid token
        If the action is to create, retrieve, list an invitation or memberships the user has to be part of the workspace
        When an invitation is accepted, the user cannot be part of a workspace
        The job title can only be changed by admin user of the workspace
        """
        user = request.user
        if user.is_anonymous:
            if view.action == 'retrieve':
                try:
                    view.get_serializer().validate_token(['token'])
                    return True
                except rest_framework.exceptions.ValidationError:
                    return False

        if view.action in ['create', 'retrieve', 'list']:
            parents = view.get_parents_query_dict()
            return user.memberships.filter(**parents).exists()

        if view.action == 'partial_update':
            if "status" in request.data:
                if request.data["status"] == "accepted":
                    return True
            elif "job_title" in request.data:
                parents = view.get_parents_query_dict()
                return user.memberships.filter(**parents, role=WS_ADMIN).exists()

        return False









