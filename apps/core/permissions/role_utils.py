from account.utils import get_workspace_membership
from core.permissions.roles import (
    AskAnnaAdmin,
    AskAnnaMember,
    AskAnnaPermissions,
    AskAnnaPublicViewer,
    BasePermissions,
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    ProjectPublicViewer,
    ProjectViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceNoMember,
    WorkspacePermissions,
    WorkspacePublicViewer,
    WorkspaceViewer,
)
from project.models import Project
from workspace.models import Workspace


def get_role_class(role_code: str) -> type[BasePermissions]:
    """Get the role class by the role code. If multiple classes have the same code, then return the first class."""
    role_mapping = {
        AskAnnaPublicViewer.code: AskAnnaPublicViewer,
        AskAnnaMember.code: AskAnnaMember,
        AskAnnaAdmin.code: AskAnnaAdmin,
        WorkspaceNoMember.code: WorkspaceNoMember,
        WorkspacePublicViewer.code: WorkspacePublicViewer,
        WorkspaceViewer.code: WorkspaceViewer,
        WorkspaceMember.code: WorkspaceMember,
        WorkspaceAdmin.code: WorkspaceAdmin,
        ProjectNoMember.code: ProjectNoMember,
        ProjectPublicViewer.code: ProjectPublicViewer,
        ProjectViewer.code: ProjectViewer,
        ProjectMember.code: ProjectMember,
        ProjectAdmin.code: ProjectAdmin,
    }

    return role_mapping[role_code]


def merge_role_permissions(roles: list) -> dict[str, bool]:
    """
    Merge the permissions of the given roles into a single list of permissions. If a permission is defined in multiple
    roles and one of the roles has the permission set to True, the permission is set to True in the merged list.
    """

    permissions = {}
    true_permissions = {}

    for role in roles:
        role_permissions = role.full_permissions()
        permissions.update(role_permissions)
        role_true_permissions = role.true_permissions()
        true_permissions.update(role_true_permissions)

    permissions.update(true_permissions)

    return dict(sorted(permissions.items()))


def get_user_role(user) -> type[AskAnnaPermissions]:
    """Returns the role for the user"""
    if user.is_active:
        if user.is_superuser:
            return AskAnnaAdmin
        return AskAnnaMember
    return AskAnnaPublicViewer


def get_user_workspace_role(user, workspace: Workspace) -> type[WorkspacePermissions]:
    """Get the role for the user in the workspace"""
    if user.is_anonymous or not user.is_active:
        if workspace.is_public:
            return WorkspacePublicViewer
        return WorkspaceNoMember

    membership = get_workspace_membership(user, workspace)
    if membership:
        role = membership.get_role()
        if role in (WorkspaceAdmin, WorkspaceMember, WorkspaceViewer):
            return role

    if workspace.is_public:
        return WorkspacePublicViewer

    return WorkspaceNoMember


def get_user_roles_for_project(user, project: Project) -> list[type[BasePermissions]]:
    """Get the roles for the user in the project"""
    workspace_role = get_user_workspace_role(user, project.workspace)
    roles: list[type[BasePermissions]] = [workspace_role]

    if workspace_role.code == WorkspaceAdmin.code and ProjectAdmin not in roles:
        roles.append(ProjectAdmin)
    elif workspace_role.code == WorkspaceMember.code and ProjectMember not in roles:
        roles.append(ProjectMember)
    elif workspace_role.code == WorkspaceViewer.code and ProjectViewer not in roles:
        roles.append(ProjectViewer)
    elif workspace_role.code == WorkspacePublicViewer.code and ProjectPublicViewer not in roles:
        roles.append(ProjectPublicViewer)
    elif workspace_role.code == WorkspaceNoMember.code and ProjectNoMember not in roles:
        roles.append(ProjectNoMember)

    return roles


def get_request_roles(
    request, project: Project | None = None, workspace: Workspace | None = None
) -> list[type[BasePermissions]]:
    """
    Get the roles for the request's user and if the project and workspace are set include the roles for those too.
    """
    user_role = get_user_role(request.user)

    if project and workspace:
        assert (
            project.workspace == workspace
        ), "The project and workspace should be the same. If not, permission could be given while it should not."

    if project:
        return [user_role] + get_user_roles_for_project(request.user, project)
    if workspace:
        return [user_role, get_user_workspace_role(request.user, workspace)]

    return [user_role]


def request_has_permission(
    request, permission: str, project: Project | None = None, workspace: Workspace | None = None
):
    roles = get_request_roles(request, project, workspace)
    request_permissions = merge_role_permissions(roles)
    return request_permissions.get(permission, False)
