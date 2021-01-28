"""Define permissions class for Job related access control."""
from rest_framework import permissions
from project.models import Project
from users.models import Membership, WS_ADMIN, WS_MEMBER

from workspace.models import Workspace
from workspace.permissions import IsWorkspaceMemberBasePermission
from uuid import UUID


class IsMemberOfProjectBasedOnPayload(permissions.BasePermission):
    """
    We check the payload for POST, PUT, PATCH requests.
    We check on the field "project" which we use to determine whether
    the user is a member of the workspace of that project
    """

    def has_permission(self, request, view):
        """
        We check access to this particular view.
        If it is a POST, check the existence of the "project" key
        """
        if view.action in ["create"]:
            # read the "project" key value
            project = request.data.get("project")
            if project:
                project_obj = Project.objects.get(short_uuid=project)
                # check whether this user has access to the project
                is_member = Membership.members.filter(
                    user=request.user, object_uuid=project_obj.workspace.uuid
                ).exists()
                return is_member
        elif view.action in ["partial_update", "put"]:
            variable = view.get_object()
            project_obj = variable.project
            # check whether this user has access to the project
            is_member = Membership.members.filter(
                user=request.user, object_uuid=project_obj.workspace.uuid
            ).exists()
            return is_member

        return False


class IsMemberOfProjectAttributePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the project."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(uuid=obj.project.workspace_id)

        if hasattr(view, "get_parents_query_dict"):
            project_suuid = view.get_parents_query_dict().get(
                "project__short_uuid", None
            )
            if project_suuid is not None:
                return Workspace.objects.filter(project__short_uuid=project_suuid)

        if view.action in ["create"]:
            project_suuid = request.data.get("project")
            return Workspace.objects.filter(project__short_uuid=project_suuid)

        return None


class IsMemberOfJobDefAttributePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the JobDef."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(uuid=obj.jobdef.project.workspace_id)

        if hasattr(view, "get_parents_query_dict"):
            jobdef_suuid = view.get_parents_query_dict().get("jobdef__short_uuid", None)
            if jobdef_suuid is not None:
                return Workspace.objects.filter(
                    project__jobdef__short_uuid=jobdef_suuid
                )
            jobrun_suuid = view.get_parents_query_dict().get("jobrun__short_uuid", None)
            if jobrun_suuid is not None:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__short_uuid=jobrun_suuid
                )

        return None


class IsMemberOfJobRunAttributePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the JobRun."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(uuid=obj.jobrun.jobdef.project.workspace_id)

        if hasattr(view, "get_parents_query_dict"):
            jobrun_suuid = view.get_parents_query_dict().get("jobrun__short_uuid", None)
            if jobrun_suuid is not None:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__short_uuid=jobrun_suuid
                )

        return None


class IsMemberOfArtifactAttributePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the Artifact."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(
                uuid=obj.artifact.jobrun.jobdef.project.workspace_id
            )

        if hasattr(view, "get_parents_query_dict"):
            jobrun_suuid = view.get_parents_query_dict().get(
                "artifact__short_uuid", None
            )
            if jobrun_suuid is not None:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__artifact__short_uuid=jobrun_suuid
                )

        if view.action in ["create"]:

            # The query fails if the value is not a valid UUID.
            # Avoid query errors :D
            try:
                artifact_uuid = UUID(request.data.get("artifact"))
            except ValueError:
                pass
            else:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__artifact__uuid=artifact_uuid
                )

        return None


class IsMemberOfJobOutputAttributePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the JobOutput."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(
                uuid=obj.joboutput.jobrun.jobdef.project.workspace_id
            )

        if hasattr(view, "get_parents_query_dict"):
            jobrun_suuid = view.get_parents_query_dict().get(
                "joboutput__short_uuid", None
            )
            if jobrun_suuid is not None:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__joboutput__short_uuid=jobrun_suuid
                )

        if view.action in ["create"]:

            # The query fails if the value is not a valid UUID.
            # Avoid query errors :D
            try:
                joboutput_uuid = UUID(request.data.get("joboutput"))
            except ValueError:
                pass
            else:
                return Workspace.objects.filter(
                    project__jobdef__jobrun__joboutput__uuid=joboutput_uuid
                )

        return None
