from rest_framework import permissions as rest_permissions


class RoleBasedPermission(rest_permissions.BasePermission):
    """
    We match the user's role(s) permissions against the defined rule set for a specific action defined in the view with
    the `rbac_permissions_by_action` attribute. If one of the user's roles has the required permission for the action,
    the user gets permission to perform the action.

    Default actions: list, retrieve, create, update, partial_update, destroy.

    Example setup:
        rbac_permissions_by_action = {
            "list": ["workspace.people.list"],
            "retrieve": ["workspace.people.list"],
            "destroy": ["workspace.people.remove"],
            "update": ["workspace.people.edit"],
        }

    The RoleBasedPermission works only on global action level. The RoleBasePermission cannot check if the user has
    permission for an instance. For example, the role based permission can give you permission to list objects, but
    cannot determine which objects the requested user has access to. A location to handle this logic is the
    `get_queryset` method of the view.
    """

    def _has_rbac_permission_in_request_user_roles(self, required_permissions, request_user_roles):
        return any(
            map(
                lambda request_user_role: any(
                    map(
                        lambda required_permission: required_permission in request_user_role.permissions(),
                        required_permissions,
                    )
                ),
                request_user_roles,
            )
        )

    def has_permission(self, request, view):
        assert (
            view.rbac_permissions_by_action is not None
        ), f"'{self.__class__.__name__}' should include a `rbac_permissions_by_action` attribute, or don't remove the "
        "'RoleBasedPermission' permission from 'permission_classes'."

        if view.action is None:
            """RoleBasedPermission works with actions. Adding actions to the view is required. For example, by
            inheriting the ViewSetMixin from 'rest_framework.viewsets'.

            If 'view.action' is None, it means that the view does not inherit the ViewSetMixin or that the method is
            not allowed. In both cases, we assume that the request has permission when 'view.action' is None."""
            return True

        assert request.user_roles is not None, "'request.user_roles' should not be None. Did you inherit the "
        "'ObjectRoleMixin'?"

        required_permissions = view.rbac_permissions_by_action.get(view.action, [])

        # If the action is not defined in the rbac_permissions_by_action, we assume that the request has permission
        return len(required_permissions) == 0 or self._has_rbac_permission_in_request_user_roles(
            required_permissions, request.user_roles
        )
