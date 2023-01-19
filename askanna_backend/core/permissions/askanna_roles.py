from typing import Dict, List


class BasePermissions:
    @classmethod
    def __object_permissions__(cls) -> Dict[str, list]:
        """
        The classmethod '__object_permissions__' return a dictionary with the permissions as keys and a list of
        roles that has the permission as values.
        """
        raise NotImplementedError("Please implement the classmethod '__object_permissions__' on the permission class")

    @classmethod
    def full_permissions(cls) -> Dict[str, bool]:
        full_permissions = {}
        for permission, roles in cls.__object_permissions__().items():
            full_permissions[permission] = cls in roles
        return full_permissions

    @classmethod
    def true_permissions(cls) -> Dict[str, bool]:
        return dict(filter(lambda x: x[1] is True, cls.full_permissions().items()))

    @classmethod
    def permissions(cls) -> List[str]:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions().items()),
            )
        )


class AskAnnaPermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> Dict[str, list]:
        return askanna_permissions


class WorkspacePermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> Dict[str, list]:
        return workspace_permissions


class ProjectPermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> Dict[str, list]:
        return project_permissions


class AskAnnaPublicViewer(AskAnnaPermissions):
    name = "AskAnna Public Viewer"
    code = "AP"


class AskAnnaMember(AskAnnaPermissions):
    name = "AskAnna Member"
    code = "AM"


class AskAnnaAdmin(AskAnnaPermissions):
    name = "AskAnna Admin"
    code = "AA"


class WorkspaceNoMember(WorkspacePermissions):
    name = "Workspace No Member"
    code = "WN"


class WorkspacePublicViewer(WorkspacePermissions):
    name = "Workspace Public Viewer"
    code = "WP"


class WorkspaceViewer(WorkspacePermissions):
    name = "Workspace Viewer"
    code = "WV"


class WorkspaceMember(WorkspacePermissions):
    name = "Workspace Member"
    code = "WM"


class WorkspaceAdmin(WorkspacePermissions):
    name = "Workspace Admin"
    code = "WA"


class ProjectPublicViewer(ProjectPermissions):
    name = "Project Public Viewer"
    code = "PP"


class ProjectNoMember(ProjectPermissions):
    name = "Project No Member"
    code = "PN"


class ProjectViewer(ProjectPermissions):
    name = "Project Viewer"
    code = "PV"


class ProjectMember(ProjectPermissions):
    name = "Project Member"
    code = "PM"


class ProjectAdmin(ProjectPermissions):
    name = "Project Admin"
    code = "PA"


askanna_permissions = {
    "askanna.admin": [
        AskAnnaAdmin,
    ],
    "askanna.member": [
        AskAnnaAdmin,
        AskAnnaMember,
    ],
    "askanna.me": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "askanna.me.edit": [
        AskAnnaAdmin,
        AskAnnaMember,
    ],
    "askanna.me.remove": [
        AskAnnaAdmin,
        AskAnnaMember,
    ],
    "workspace.create": [
        AskAnnaAdmin,
        AskAnnaMember,
    ],
    "workspace.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "workspace.people.invite.accept": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "project.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "project.code.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "project.job.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "project.run.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
    "variable.list": [
        AskAnnaAdmin,
        AskAnnaMember,
        AskAnnaPublicViewer,
    ],
}

workspace_permissions = {
    "workspace.remove": [
        WorkspaceAdmin,
    ],
    "workspace.me.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        WorkspacePublicViewer,
    ],
    "workspace.info.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        WorkspacePublicViewer,
    ],
    "workspace.info.edit": [
        WorkspaceAdmin,
    ],
    "workspace.me.edit": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
    ],
    "workspace.me.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
    "workspace.people.list": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
    ],
    "workspace.people.edit": [
        WorkspaceAdmin,
    ],
    "workspace.people.remove": [
        WorkspaceAdmin,
    ],
    "workspace.people.invite.info": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
    "workspace.people.invite.create": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
    "workspace.people.invite.remove": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
    "workspace.people.invite.resend": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
    "project.create": [
        WorkspaceAdmin,
        WorkspaceMember,
    ],
}

project_permissions = {
    "project.me.view": [
        ProjectAdmin,
        ProjectMember,
        ProjectViewer,
        ProjectPublicViewer,
    ],
    "project.info.view": [
        ProjectAdmin,
        ProjectMember,
        ProjectViewer,
        ProjectPublicViewer,
    ],
    "project.info.edit": [
        ProjectAdmin,
    ],
    "project.remove": [
        ProjectAdmin,
    ],
    "project.code.create": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.create": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.edit": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.job.remove": [
        ProjectAdmin,
        ProjectMember,
    ],
    "variable.create": [
        ProjectAdmin,
        ProjectMember,
    ],
    "variable.edit": [
        ProjectAdmin,
        ProjectMember,
    ],
    "variable.remove": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.create": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.edit": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.run.remove": [
        ProjectAdmin,
        ProjectMember,
    ],
}


def get_role_class(role_code: str):
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


def merge_role_permissions(roles: list) -> Dict[str, bool]:
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
