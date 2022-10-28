from core.permissions import ProjectMember, ProjectNoMember, RoleBasedPermission
from core.views import ObjectRoleMixin, workspace_to_project_role
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from job.models import JobDef
from job.serializers import JobSerializer
from project.models import Project
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import MSP_WORKSPACE, Membership


class JobObjectRoleMixin:
    def get_object_workspace(self):
        return self.current_object.project.workspace

    def get_object_project(self):
        return self.current_object.project

    def get_workspace_role(self, user, *args, **kwargs):
        return Membership.get_workspace_role(user, self.get_object_workspace())

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        or the project and workspace are public
        """
        user = self.request.user

        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
                .order_by("name")
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__in=member_of_workspaces)
                | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        )


class JobActionView(
    JobObjectRoleMixin,
    ObjectRoleMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobDef.jobs.active()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.job.list"],
        "retrieve": ["project.job.list"],
        "create": ["project.job.create"],
        "destroy": ["project.job.remove"],
        "update": ["project.job.edit"],
        "partial_update": ["project.job.edit"],
    }

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()


class ProjectJobViewSet(
    JobObjectRoleMixin,
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """
    This is a duplicated viewset like `JobActionView` but ReadOnly version
    """

    queryset = JobDef.jobs.active()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.job.list"],
        "retrieve": ["project.job.list"],
    }

    def get_list_role(self, request, *args, **kwargs):
        """
        Get list permision based on the project_suuid from the url
        """
        project_suuid = kwargs.get("parent_lookup_project__short_uuid")
        try:
            project = Project.objects.get(short_uuid=project_suuid)
        except ObjectDoesNotExist:
            raise Http404

        workspace_role, request.membership = Membership.get_workspace_role(request.user, project.workspace)
        request.user_roles.append(workspace_role)
        request.object_role = workspace_role

        # try setting a project role based on workspace role
        if workspace_to_project_role(workspace_role) is not None:
            inherited_role = workspace_to_project_role(workspace_role)
            request.user_roles.append(inherited_role)

        return Membership.get_project_role(request.user, project)
