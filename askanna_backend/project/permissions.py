"""Define permissions class for Project related access control."""
from workspace.permissions import IsWorkspaceMemberBasePermission
from workspace.models import Workspace


class IsMemberOfProjectWorkspacePermission(IsWorkspaceMemberBasePermission):
    """Grant access if the user is member of the Workspace of the project."""

    def get_workspace_queryset(self, request, view, obj=None):
        """Queryset for the workspace for the current project."""
        if obj:
            return Workspace.objects.filter(uuid=obj.workspace_id)

        if hasattr(view, "get_parents_query_dict"):
            workspace_suuid = view.get_parents_query_dict().get("workspace__short_uuid", None)
            if workspace_suuid is not None:
                return Workspace.objects.filter(short_uuid=workspace_suuid)

        if view.action in ["create"]:
            workspace_suuid = request.data.get("workspace")
            return Workspace.objects.filter(short_uuid=workspace_suuid)

        return None
