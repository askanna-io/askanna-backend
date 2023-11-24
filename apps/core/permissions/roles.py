class BasePermissions:
    name: str
    code: str

    @classmethod
    def __object_permissions__(cls) -> dict[str, list]:
        """
        The classmethod '__object_permissions__' return a dictionary with the permissions as keys and a list of
        roles that has the permission as values.
        """
        raise NotImplementedError("Please implement the classmethod '__object_permissions__' on the permission class")

    @classmethod
    def full_permissions(cls) -> dict[str, bool]:
        full_permissions = {}
        for permission, roles in cls.__object_permissions__().items():
            full_permissions[permission] = cls in roles
        return full_permissions

    @classmethod
    def true_permissions(cls) -> dict[str, bool]:
        return dict(filter(lambda x: x[1] is True, cls.full_permissions().items()))

    @classmethod
    def permissions(cls) -> list[str]:
        return list(
            map(
                lambda y: y[0],
                filter(lambda x: x[1], cls.full_permissions().items()),
            )
        )


class AskAnnaPermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> dict[str, list]:
        return askanna_permissions


class WorkspacePermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> dict[str, list]:
        return workspace_permissions


class ProjectPermissions(BasePermissions):
    @classmethod
    def __object_permissions__(cls) -> dict[str, list]:
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


class ProjectNoMember(ProjectPermissions):
    name = "Project No Member"
    code = "PN"


class ProjectPublicViewer(ProjectPermissions):
    name = "Project Public Viewer"
    code = "PP"


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
    "workspace.info.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        WorkspacePublicViewer,
    ],
    "workspace.info.edit": [
        WorkspaceAdmin,
    ],
    "workspace.me.view": [
        WorkspaceAdmin,
        WorkspaceMember,
        WorkspaceViewer,
        WorkspacePublicViewer,
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
    "project.code.view": [
        ProjectAdmin,
        ProjectMember,
        ProjectViewer,
        ProjectPublicViewer,
    ],
    "project.code.create": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.code.edit": [
        ProjectAdmin,
        ProjectMember,
    ],
    "project.code.list": [
        ProjectAdmin,
    ],
    "project.code.remove": [
        ProjectAdmin,
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
    # TODO: rename variable to project.variable
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
