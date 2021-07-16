"""Define permissions class for Workspace related access control."""
from rest_framework import permissions

from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace


class IsWorkspaceMemberBasePermission(permissions.BasePermission):
    """
    Grant access if user is member of a workspace.

    To be subclassed to provide the method that extracts the workspace to use.
    """

    membership_queryset = Membership.members.members()

    def get_workspace_queryset(self, request, view, obj=None):
        """Return a queryset that returns a single workspace to check access with."""
        if obj:
            return Workspace.objects.filter(uuid=obj.uuid)

        return None

    def _has_workspace_permission(self, request, view, obj=None):
        user = request.user
        if user.is_anonymous:
            return False

        workspace_uuid_qs = self.get_workspace_queryset(request, view, obj)
        # If a workspace queryset was returned grant access based on its membership.
        if workspace_uuid_qs is not None:
            return self.membership_queryset.filter(
                object_uuid=workspace_uuid_qs.values("uuid")[:1],
                object_type=MSP_WORKSPACE,
                user=user,
                deleted__isnull=True,
            ).exists()

        # For listings when we do not know the workspace, then grant access and let the
        # view filter the results.
        if view.action == "list":
            return True

        # At this point there was not enough information to make a decission without an object.
        # Grant access and let the second pass with an object decide.
        if not obj and view.action in [
            "retrieve",
            "update",
            "partial_update",
            "destroy",
        ]:
            return True

        # Deny at the end by default.
        return False

    def has_permission(self, request, view):
        """Return `True` if the user is a member of the workspace.
        Or we are accessing a subview where view.detail == True"""
        return self._has_workspace_permission(request, view) or (
            view.detail and not request.user.is_anonymous
        )

    def has_object_permission(self, request, view, obj):
        """Return `True` if the user is a member of the workspace."""
        return self._has_workspace_permission(request, view, obj)


class IsWorkspaceAdminBasePermission(IsWorkspaceMemberBasePermission):
    """
    Grant access if user is admin of a workspace.

    To be subclassed to provide the method that extracts the workspace to use.
    """

    membership_queryset = Membership.members.admins()
