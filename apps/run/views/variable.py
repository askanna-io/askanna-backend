from django.db.models import Q
from django.http import Http404
from django_filters import CharFilter, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from account.models.membership import MSP_WORKSPACE
from core.filters import filter_array, filter_multiple
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.askanna import RoleBasedPermission
from core.permissions.role_utils import get_user_roles_for_project
from core.viewsets import AskAnnaGenericViewSet
from run.models import Run, RunVariable, RunVariableMeta
from run.serializers.variable import RunVariableSerializer, RunVariableUpdateSerializer


class RunVariableObjectMixin(ObjectRoleMixin):
    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.run.list"],
        "partial_update": ["project.run.edit"],
    }

    def get_parrent_roles(self, request, *args, **kwargs):
        run_suuid = self.kwargs["parent_lookup_run__suuid"]
        try:
            run = Run.objects.active().get(suuid=run_suuid)
        except Run.DoesNotExist as exc:
            raise Http404 from exc

        return get_user_roles_for_project(request.user, run.jobdef.project)


class RunVariableFilterSet(FilterSet):
    run_suuid = CharFilter(
        field_name="run__suuid",
        method=filter_multiple,
        help_text="Filter run variables on a run suuid or multiple run suuids via a comma seperated list.",
    )
    job_suuid = CharFilter(
        field_name="run__jobdef__suuid",
        method=filter_multiple,
        help_text="Filter run variables on a job suuid or multiple job suuids via a comma seperated list.",
    )
    project_suuid = CharFilter(
        field_name="run__jobdef__project__suuid",
        method=filter_multiple,
        help_text="Filter run variables on a project suuid or multiple project suuids via a comma seperated list.",
    )
    workspace_suuid = CharFilter(
        field_name="run__jobdef__project__workspace__suuid",
        method=filter_multiple,
        help_text="Filter run variables on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )

    variable_name = CharFilter(field_name="variable__name")
    variable_value = CharFilter(field_name="variable__value")
    variable_type = CharFilter(field_name="variable__type")

    label_name = CharFilter(field_name="label__*__name", method=filter_array)
    label_value = CharFilter(field_name="label__*__value", method=filter_array)
    label_type = CharFilter(field_name="label__*__type", method=filter_array)


class RunVariableView(
    RunVariableObjectMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    AskAnnaGenericViewSet,
):
    """List variables"""

    queryset = RunVariable.objects.all()
    max_page_size = 10000  # For variable listings we want to allow "a lot" of data in a single request
    search_fields = ["variable__name"]
    ordering_fields = [
        "created_at",
        "variable.name",
        "variable.value",
        "variable.type",
    ]
    filterset_class = RunVariableFilterSet

    serializer_class = RunVariableSerializer

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_queryset(self):
        """
        For listings return only values from runs in projects where the current user has access to
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


class RunVariableUpdateView(
    RunVariableObjectMixin,
    NestedViewSetMixin,
    PartialUpdateModelMixin,
    AskAnnaGenericViewSet,
):
    """Update the variables for a run"""

    queryset = RunVariableMeta.objects.all()
    lookup_field = "run__suuid"
    serializer_class = RunVariableUpdateSerializer

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_queryset(self):
        """
        For listings return only values from runs in projects where the current user has access to
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

    @extend_schema(
        responses={200: None},
    )
    def partial_update(self, request, *args, **kwargs):
        super().partial_update(request, *args, **kwargs)
        # TODO: change status code to 204 BUT also change CLI to handle 204
        return Response(None, 200)
