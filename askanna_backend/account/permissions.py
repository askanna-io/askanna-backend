from account.models import Invitation
from rest_framework import exceptions, permissions


class RoleUpdateByAdminOnlyPermission(permissions.BasePermission):
    """
    This permission class is to make sure that the role can only be changed by admin accounts of the workspace. An
    admin can change anyones role except its own role.

    Important: use this permission in addition to RequestHasAccessToMembershipPermission.
    """

    def has_object_permission(self, request, view, obj):
        """
        Validate access when role is part of the payload.
        """
        if "role" in request.data or "role_code" in request.data:
            return request.user.is_authenticated and request.user != obj.user and view.request_user_is_workspace_admin

        return True


class RequestHasAccessToMembershipPermission(permissions.BasePermission):
    """
    This permission class is to make sure that the user can create, access, modify or delete a membership.
    """

    def has_permission(self, request, view):
        """
        If the action is to create, retrieve, list an invitation or memberships the user has to be
        part of the workspace. When the request is to accept an invitation, the user cannot be part of a workspace so
        we only check if it is an authenticated request.
        """
        if view.action in [
            "invite_accept",
        ]:
            return request.user.is_authenticated

        return view.request_user_is_workspace_member

    def has_object_permission(self, request, view, obj):
        """
        Removing an invitation can be done by workspace members. Removing of workspace membership can only by done by
        workspace admins.

        Membership updates can only be done by the membership owner or by admin accounts of the workspace.

        For other requests, the user has to have a workspace membership.
        """
        has_permission = view.request_user_is_workspace_member

        if view.action == "destroy":
            try:
                has_permission = obj.invitation and view.request_user_is_workspace_member
            except Invitation.DoesNotExist:
                has_permission = view.request_user_is_workspace_admin and obj.user != request.user

        elif view.action in ["partial_update", "avatar"]:
            has_permission = (not obj.deleted_at and obj.user == request.user) or view.request_user_is_workspace_admin

        elif view.action == "invite_accept":
            has_permission = request.user.is_authenticated

        return has_permission


class RequestIsValidInvite(permissions.BasePermission):
    """
    This permission is set in place to allow anonymous and non-members to request the workspace/people endpoint to get
    details on the invite.

    Requires one to pass the `token` in the query_parameters set in a GET request
    """

    def has_permission(self, request, view):
        """
        Grant access to non member that supply a token even if invalid.
        """
        user = request.user
        parents = view.get_parents_query_dict()
        not_member = user.is_anonymous or not user.memberships.filter(**parents).exists()

        return not_member and request.method == "GET" and "token" in request.query_params

    def has_object_permission(self, request, view, obj):
        """
        On instance level, check that the token is valid.
        """
        # Since this permission might be used alongside other permission classes with an OR operator, we recheck that
        # this one granted access to the view. If not granted by this class, reject the request and let other chained
        # permission classes handle it.
        if not self.has_permission(request, view):
            return False

        token = request.query_params.get("token")
        try:
            view.get_serializer(instance=obj).validate_token(token)
        except exceptions.ValidationError:
            return False
        else:
            return True


class IsOwnerOfUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return not (request.user.is_anonymous) and (obj.uuid == request.user.uuid)


class IsNotMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return not request.user.is_active
