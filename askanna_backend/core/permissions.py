# -*- coding: utf-8 -*-
import typing
from rest_framework import permissions

"""
core.types

Types representing roles of a user. A user can have different roles depending on the context.
A user can hold many types within the same context.

"""


class BaseRoleType(metaclass=type):
    def __permissions_list(cls) -> typing.Dict:
        return global_permissions

    def full_permissions(cls) -> typing.Dict:
        my_permissions = {}
        for permission, members in cls.__permissions_list(cls).items():
            my_permissions[permission] = cls in members
        return my_permissions

    @classmethod
    def permissions(cls) -> typing.List:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions(cls).items()),
            )
        )


class AskAnnaMember(BaseRoleType):
    name = "AskAnna Member"
    code = "AM"
    prio = 2


class AskAnnaAdmin(BaseRoleType):
    name = "AskAnna Admin"
    code = "AA"
    prio = 0


class WorkspacePermissions(BaseRoleType):
    def __permissions_list(cls) -> typing.Dict:
        permissions = workspace_permissions
        permissions.update(**project_permissions)  # also include project permissions
        return permissions

    def full_permissions(cls) -> typing.Dict:
        my_permissions = {}
        for permission, members in cls.__permissions_list(cls).items():
            my_permissions[permission] = cls in members
        return my_permissions

    @classmethod
    def permissions(cls) -> typing.List:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions(cls).items()),
            )
        )


class WorkspaceNoMember(WorkspacePermissions):
    name = "Workspace No Member"
    code = "WN"
    prio = 999


class WorkspaceViewer(WorkspacePermissions):
    name = "Workspace Viewer"
    code = "WV"
    prio = 799


class WorkspaceMember(WorkspacePermissions):
    name = "Workspace Member"
    code = "WM"
    prio = 102


class WorkspaceAdmin(WorkspacePermissions):
    name = "Workspace Admin"
    code = "WA"
    prio = 100


class ProjectPermissions(BaseRoleType):
    def __permissions_list(cls) -> typing.Dict:
        return project_permissions

    def full_permissions(cls) -> typing.Dict:
        my_permissions = {}
        for permission, members in cls.__permissions_list(cls).items():
            my_permissions[permission] = cls in members
        return my_permissions

    @classmethod
    def permissions(cls) -> typing.List:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions(cls).items()),
            )
        )


class ProjectNoMember(ProjectPermissions):
    name = "Project No Member"
    code = "PN"
    prio = 999


class ProjectMember(ProjectPermissions):
    name = "Project Member"
    code = "PM"
    prio = 202


class ProjectAdmin(ProjectPermissions):
    name = "Project Admin"
    code = "PA"
    prio = 200


class PublicPermissions(BaseRoleType):
    def __permissions_list(cls) -> typing.Dict:
        _permissions = workspace_permissions
        _permissions.update(**project_permissions)  # also include project permissions
        _permissions.update(**global_permissions)  # also include global permissions
        return _permissions

    def full_permissions(cls) -> typing.Dict:
        my_permissions = {}
        for permission, members in cls.__permissions_list(cls).items():
            my_permissions[permission] = cls in members
        return my_permissions

    @classmethod
    def permissions(cls) -> typing.List:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions(cls).items()),
            )
        )


class PublicViewer(PublicPermissions):
    """
    This role is to work on user anonymous and public workspaces or projects
    """

    name = "AskAnna Public Viewer"
    code = "AN"
    prio = 999


global_permissions = {
    "askanna.me": [PublicViewer, AskAnnaAdmin, AskAnnaMember],
    "askanna.admin": [AskAnnaAdmin],
    "askanna.member": [AskAnnaAdmin, AskAnnaMember],
    "askanna.workspace.create": [AskAnnaAdmin, AskAnnaMember],
}

workspace_permissions = {
    "workspace.me.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        PublicViewer,
    ],  # allows for viewing workspace profile
    # both WorkspaceAdmin and WorkspaceMember are added as one can assume 1 role at a time.
    # Meaning in order to let WorkspaceAdmin view/edit/delete it's own profile
    # we must have WorkspaceAdmin listed here
    # WorkspaceViewer must also be listed here to return the permissions the viewer has on this workspace
    "workspace.me.edit": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
    ],  # allows for editing workspace profile
    "workspace.me.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],  # allow self deletion from a workspace
    "workspace.info.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        PublicViewer,
    ],
    "workspace.info.edit": [WorkspaceAdmin],
    "workspace.remove": [WorkspaceAdmin],
    "workspace.project.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        PublicViewer,  # view will handle showing correct PUBLIC items
    ],  # only used for API consumers
    "workspace.project.create": [WorkspaceAdmin, WorkspaceMember],
    "workspace.people.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        # PublicViewer, # disabled because of people names with e-mail in name
    ],  # only used for API consumers
    "workspace.people.invite.create": [WorkspaceAdmin, WorkspaceMember],
    "workspace.people.invite.resend": [WorkspaceAdmin, WorkspaceMember],
    "workspace.people.edit": [WorkspaceAdmin],
    "workspace.people.remove": [WorkspaceAdmin],
}

project_permissions = {
    "project.me.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,
    ],
    "project.info.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,  # view will handle showing correct PUBLIC items
    ],
    "project.info.edit": [WorkspaceAdmin, ProjectAdmin],
    "project.remove": [WorkspaceAdmin, ProjectAdmin],
    "project.code.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,
    ],
    "project.code.create": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,
    ],
    "project.job.create": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.edit": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.variable.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,
    ],
    "project.variable.create": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.variable.edit": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.variable.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        ProjectAdmin,
        ProjectMember,
        PublicViewer,
    ],
    "project.run.create": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.edit": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
        ProjectAdmin,
        ProjectMember,
    ],
}


class BaseRoleBasedPermission(permissions.BasePermission):
    """
    We match the user's role agains the defined a boolean based
    rule set for a specific action (CREATE/READ/UPDATE/DELETE and LIST)
    defined in the view with `RBAC_BY_ACTION`

    Default do not grant permission (return False)

    This works only on global action level, on instance level we must implement
    ownership rules (use other permissions for this)

    List permissions (`has_permission`) are incomplete and only determines whether to
    have "general" access, not on object level in the list. `get_queryset` should
    include the logic of ownership or visibility.

    """

    def _has_permission_in_roles(self, roles, required_permissions):
        return any(
            map(
                lambda role: any(map(lambda x: x in role.permissions(), required_permissions)),
                roles,
            )
        )

    def _has_required_permissions(self, request, view, obj=None):
        RBAC_BY_ACTION = getattr(view, "RBAC_BY_ACTION") or {}
        if hasattr(view, "action") and view.action:
            # the view is using a ViewSetMixin, only the `ViewSetMixin` sets the view.action
            action_or_method = view.action.lower()
        else:
            action_or_method = request.method.lower()
        required_permissions = RBAC_BY_ACTION.get(action_or_method, [])

        # when no limiting permission is defined, we assume there is no restriction
        approved = len(required_permissions) == 0 or self._has_permission_in_roles(
            request.user_roles, required_permissions
        )
        return approved

    def has_permission(self, request, view):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return self._has_required_permissions(request, view)

    def has_object_permission(self, request, view, obj):
        """
        Return `True` if permission is granted, `False` otherwise.
        """
        return self._has_required_permissions(request, view, obj)


class RoleBasedPermission(BaseRoleBasedPermission):
    ...
