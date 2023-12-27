import warnings

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import permissions

from core.permissions.role_utils import request_has_permission
from core.viewsets import AskAnnaGenericViewSet


class AskAnnaPermissionByAction(permissions.BasePermission):
    """
    On the model level, we can define permissions for specific actions. For example, we can define that a user can
    create a project, but not update it. This is done by defining a `permission_by_action` property on the model.

    The `permission_by_action` property is a dictionary where the key is the action or a tuple with actions, and the
    value is the permission.

    Example setup:
        class Project(BaseModel):
            permission_by_action = {
                "list": "project.code.list",
                ("retrieve", "storage_file_info", "storage_file_download"): "project.code.view",
            }

            # Other model code

    Given the context of a request, a check is done if the user has permission to perform the action. This is done by
    looking up the request's user roles and check if one of the roles has the required permission. The request's user
    roles are filtered by the project and/or workspace of the requested object and/or action.

    For example, if we want to create a new object in relation to a project, we first check which roles the user has
    for the project. Next, we look-up which roles are required to perform the action. If one of the user's roles has
    the required permission, the user has permission to perform the action.
    """

    def _get_permission(self, obj, action) -> str:
        for key, value in obj.permission_by_action.items():
            if key == action or (isinstance(key, tuple) and action in key):
                return value

        raise KeyError(f"Action '{action}' not found in 'permission_by_action'.")

    def has_permission(self, request, view, action_prefix: str | None = None):
        assert isinstance(view, AskAnnaGenericViewSet), "View needs to inherrit from AskAnnaGenericViewSet"

        # When the view has a detail attribute, we need to check if the user has permission to the object. This is
        # handle by 'has_object_permission'.
        if view.detail:
            return True

        serializer_class = view.get_serializer_class()
        model = serializer_class.Meta.model

        if request.method in permissions.SAFE_METHODS:
            method_name = "request_has_read_permission"
        else:
            method_name = "request_has_write_permission"

        if hasattr(model, method_name) and hasattr(model, "permission_by_action"):
            warnings.warn(
                f"Both 'permission_by_action' and '{method_name}' are defined. The '{method_name}' will be used.",
                stacklevel=1,
            )

        if hasattr(model, method_name):
            return getattr(model, method_name)(request, view)

        if hasattr(model, "permission_by_action"):
            action = f"{action_prefix}_{view.action}" if action_prefix else view.action
            permission = self._get_permission(model, action)

            try:
                project = view.get_parrent_project(request=request) if hasattr(view, "get_parrent_project") else None
            except ObjectDoesNotExist:
                return False

            return request_has_permission(request, permission, project=project)

        raise NotImplementedError(
            f"Model '{model._meta.app_label}.{model._meta.object_name}' does not have a method '{method_name}' or "
            "property 'permission_by_action'."
        )

    def has_object_permission(self, request, view, obj, action_prefix: str | None = None):
        if request.method in permissions.SAFE_METHODS:
            method_name = "request_has_object_read_permission"
        else:
            method_name = "request_has_object_write_permission"

        if hasattr(obj, method_name) and hasattr(obj, "permission_by_action"):
            warnings.warn(
                f"Both 'permission_by_action' and '{method_name}' are defined. The '{method_name}' will be used",
                stacklevel=1,
            )

        if hasattr(obj, method_name):
            return getattr(obj, method_name)(request, view)

        if hasattr(obj, "permission_by_action"):
            action = f"{action_prefix}_{view.action}" if action_prefix else view.action
            permission = self._get_permission(obj, action)

            project = obj.project if hasattr(obj, "project") else None
            workspace = obj.workspace if hasattr(obj, "workspace") else None

            return request_has_permission(request, permission, project=project, workspace=workspace)

        raise NotImplementedError(
            f"Model '{obj._meta.app_label}.{obj._meta.object_name}' does not have a method '{method_name}' or "
            "property 'permission_by_action'."
        )


class RoleBasedPermission(permissions.BasePermission):
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

    def _has_rbac_permission_in_request_user_roles(self, view, request_user_roles):
        required_permissions = view.rbac_permissions_by_action.get(view.action, [])
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

        assert (
            view.action is not None
        ), f"'{self.__class__.__name__}' should include an 'action' attribute. Did you inherit the 'ViewSetMixin'?"

        return self._has_rbac_permission_in_request_user_roles(view, request.user_roles)
