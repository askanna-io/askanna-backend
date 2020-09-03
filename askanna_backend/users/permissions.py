from rest_framework import permissions
from users.models import Membership, WS_ADMIN, WS_MEMBER


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
            members.filter(user=request.user, role__in=self.required_roles).count() > 0
        )

    def has_object_permission(self, request, view, obj):

        # can the user modify the object (row based access)
        # is the user an admin
        # specific rules to modify specific fields can be defined later in serializer
        # this permission only checks access
        members = view.get_queryset()
        is_admin = members.filter(user=request.user, role=WS_ADMIN).count() > 0

        return obj.user == request.user or is_admin


class IsMemberOrAdminUser(permissions.BasePermission):
    required_roles = [WS_ADMIN, WS_MEMBER]

    def has_permission(self, request, view):
        # is this user part of the queryset in the view?
        # in other words, is this user part of the Model
        members = view.get_queryset()
        return (
            members.filter(user=request.user, role__in=self.required_roles).count() > 0
        )

    def has_object_permission(self, request, view, obj):

        # can the user modify the object (row based access)
        # is owner or is admin
        # specific rules to modify specific fields can be defined later in serializer
        # this permission only checks access
        members = view.get_queryset()
        is_admin = members.filter(user=request.user, role=WS_ADMIN).count() > 0

        return obj.user == request.user or is_admin
