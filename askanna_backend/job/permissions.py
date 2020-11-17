from rest_framework import permissions
from project.models import Project
from users.models import Membership, WS_ADMIN, WS_MEMBER
from django.db.models import Q
import rest_framework


class IsMemberOfProjectBasedOnPayload(permissions.BasePermission):
    """
    We check the payload for POST, PUT, PATCH requests.
    We check on the field "project" which we use to determine whether the user is a member of the workspace of that project
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
