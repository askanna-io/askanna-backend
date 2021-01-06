import rest_framework
from rest_framework import permissions

from users.models import WS_ADMIN, Invitation


class RoleUpdateByAdminOnlyPermission(permissions.BasePermission):
    """
    This permission class is to make sure that the role can only be changed by admin users of the workspace
    An admin can change anyones role except its own role.

    It is important to use it IN ADDITION to RequestHasAccessToMembershipPermission:
    Example:
    ```
    RequestHasAccessToMembershipPermission & RoleUpdateByAdminOnlyPermission
    ```
    """

    def has_object_permission(self, request, view, obj):
        """
        Validate access when role is part of the payload.

        Otherwise allow as we have no business in the request.
        """
        if "role" in request.data:

            parents = view.get_parents_query_dict()
            user = request.user
            return (
                user.is_authenticated
                and user != obj.user
                and user.memberships.filter(**parents, role=WS_ADMIN).exists()
            )

        return True


class RequestHasAccessToMembershipPermission(permissions.BasePermission):
    """
    This permission class is to make sure that the user can create, access, modify or delete a membership.
    """

    def has_permission(self, request, view):
        """
        If the action is to create, retrieve, list an invitation or memberships the user has to be part of the workspace
        When an invitation is accepted, the user cannot be part of a workspace
        """
        user = request.user

        if view.action in ["partial_update", "destroy"]:
            # Let has_object_permission deal with this request.
            return user.is_authenticated

        if view.action in ["create", "retrieve", "list"]:
            parents = view.get_parents_query_dict()
            is_member = (
                user.is_authenticated
                and user.memberships.filter(deleted__isnull=True, **parents).exists()
            )
            return is_member

        return False

    def has_object_permission(self, request, view, obj):
        """
        The job title can only be changed by admin user of the workspace.
        Otherwise access is granted to members.
        """
        user = request.user
        parents = view.get_parents_query_dict()
        # member_role is a tuple with the role.
        member_role = (
            user.memberships.filter(deleted__isnull=True, **parents)
            .values_list("role")
            .first()
        )
        is_member = bool(member_role)
        is_admin = is_member and WS_ADMIN in member_role

        if view.action == "destroy":
            try:
                return obj.invitation and is_member
            except Invitation.DoesNotExist:
                return is_admin and obj.user != user

        if view.action == "partial_update":
            if request.data.get("status") == "accepted":
                # Let the serializer validate if a user can accept an invitation.
                return user.is_authenticated

            if request.data.get("status") == "invited":
                return is_member

            return (not obj.deleted and obj.user == request.user) or is_admin

        return is_member


class RequestIsValidInvite(permissions.BasePermission):
    """
    This permission is set in place to allow anonymous and non-members to request the
    workspace/people endpoint to get details on the invite.

    Requires one to pass the `token` in the query_parameters set in a GET request

    Both global and object check has to be implemented:

    - Specific check on whether the `token` matches the invite on a `retrieve` action
    """

    def has_permission(self, request, view):
        """
        Grant access to non member that supply a token  even if invalid.
        """
        user = request.user
        parents = view.get_parents_query_dict()
        not_member = (
            user.is_anonymous or not user.memberships.filter(**parents).exists()
        )
        return (
            not_member and view.action == "retrieve" and "token" in request.query_params
        )

    def has_object_permission(self, request, view, obj):
        """
        On instance level, check that the token is valid.
        """
        # Since this permission is used alongside other permission classes
        # with an OR operator, we recheck that this one granted access
        # to the view. If not granted by this class, reject the request
        # and let other chained permission classes handle it.
        if not self.has_permission(request, view):
            return False

        token = request.query_params.get("token")
        try:
            view.get_serializer(instance=obj).validate_token(token)
        except rest_framework.exceptions.ValidationError:
            return False
        else:
            return True


class IsOwnerOfUser(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return not (request.user.is_anonymous) and (
            obj.uuid == request.user.uuid or request.user.is_superuser
        )


class IsNotAlreadyMember(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        Exclude existing members from this particular view/action
        Only superuser can access still
        """
        is_member = request.user.is_anonymous is not True
        is_admin = request.user.is_superuser
        return not is_member or is_admin
