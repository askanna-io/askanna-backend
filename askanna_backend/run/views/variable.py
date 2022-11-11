from core.permissions import ProjectNoMember, RoleBasedPermission
from core.views import ObjectRoleMixin
from django.db.models import Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from project.models import Project
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from run.filters import RunVariableFilter
from run.models import Run, RunVariable, RunVariableRow
from run.serializers import RunVariableRowSerializer, RunVariableSerializer
from users.models import MSP_WORKSPACE, Membership


class RunVariableObjectMixin:
    permission_classes = [RoleBasedPermission]
    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "create": ["project.run.create"],
        "destroy": ["project.run.remove"],
        "update": ["project.run.edit"],
        "partial_update": ["project.run.edit"],
    }

    def get_object_workspace(self):
        return self.get_object_project().workspace

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        project = None
        if kwargs.get("parent_lookup_run_suuid"):
            run = Run.objects.get(suuid=kwargs.get("parent_lookup_run_suuid"))
            project = run.jobdef.project
        elif kwargs.get("parent_lookup_run__suuid"):
            run = Run.objects.get(suuid=kwargs.get("parent_lookup_run__suuid"))
            project = run.jobdef.project
        if project:
            request.user_roles += Membership.get_roles_for_project(request.user, project)
        else:
            raise Http404

        # by default return NoMember role
        return ProjectNoMember, None


class RunVariableView(
    RunVariableObjectMixin,
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Update the variables for a run"""

    # we removed 'put' from the http_method_names as we don't suppor this in this view
    # - post and delete
    http_method_names = ["get", "patch", "head", "options", "trace"]

    queryset = RunVariable.objects.all()
    lookup_field = "run__suuid"  # not needed for listviews
    serializer_class = RunVariableSerializer

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(run__jobdef__project__workspace__in=member_of_workspaces)
                | (
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )
        )

    # Override because we don't return the full object, just the `variables` field
    def update(self, request, *args, **kwargs):
        _ = kwargs.pop("partial", False)
        instance = self.get_object()
        instance.variables = request.data.get("variables", [])
        instance.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        instance.refresh_from_db()
        return Response(instance.variables)


class RunVariableRowView(
    RunVariableObjectMixin,
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List variables"""

    queryset = RunVariableRow.objects.all()
    lookup_field = "suuid"  # not needed for listviews
    serializer_class = RunVariableRowSerializer

    # Override default, remove OrderingFilter because we use the DjangoFilterBackend version
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RunVariableFilter

    def get_object_workspace(self):
        return self.get_object_project().workspace

    def get_object_project(self):
        return Project.objects.get(suuid=self.current_object.project_suuid)

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace

        # this one is a bit special as the RunVariableRows are not in the same
        database as the "main" database where Workspace and Project are stored

        Here we can use a specific query where we know the `run_suuid` (because this is in the url)
        and saved as parameter in kwargs (`parent_lookup_run_suuid`)

        """
        user = self.request.user
        run = Run.objects.get(suuid=self.kwargs.get("parent_lookup_run_suuid"))

        if user.is_anonymous and (
            (run.jobdef.project.visibility == "PUBLIC" and run.jobdef.project.workspace.visibility == "PUBLIC")
        ):
            return super().get_queryset().filter(run_suuid=self.kwargs.get("parent_lookup_run_suuid"))
        elif user.is_anonymous:
            # return empty query_set because the anonymous user doesn't have access
            return super().get_queryset().none()

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)
        member_of_projects = (
            Project.objects.filter(
                Q(workspace_id__in=member_of_workspaces) | (Q(workspace__visibility="PUBLIC") & Q(visibility="PUBLIC"))
            ).values_list("suuid", flat=True)
        )[
            ::-1
        ]  # hard convert to list for cross db query
        return super().get_queryset().filter(Q(project_suuid__in=member_of_projects))
