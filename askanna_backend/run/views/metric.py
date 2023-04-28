from django.db.models import Q
from django.http import Http404
from django_filters import CharFilter, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from account.models.membership import MSP_WORKSPACE, Membership
from core.filters import filter_array, filter_multiple
from core.mixins import ObjectRoleMixin, UpdateModelWithoutPartialUpateMixin
from core.permissions.role import RoleBasedPermission
from run.models import Run, RunMetric, RunMetricMeta
from run.serializers.metric import RunMetricSerializer, RunMetricUpdateSerializer


class RunMetricObjectMixin(ObjectRoleMixin):
    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.run.list"],
        "update": ["project.run.edit"],
    }

    def get_parrent_roles(self, request, *args, **kwargs):
        run_suuid = self.kwargs["parent_lookup_run__suuid"]
        try:
            run = Run.objects.active().get(suuid=run_suuid)
        except Run.DoesNotExist as exc:
            raise Http404 from exc

        return Membership.get_roles_for_project(request.user, run.jobdef.project)


class RunMetricFilterSet(FilterSet):
    run_suuid = CharFilter(
        field_name="run__suuid",
        method=filter_multiple,
        help_text="Filter run metrics on a run suuid or multiple run suuids via a comma seperated list.",
    )
    job_suuid = CharFilter(
        field_name="run__jobdef__suuid",
        method=filter_multiple,
        help_text="Filter run metrics on a job suuid or multiple job suuids via a comma seperated list.",
    )
    project_suuid = CharFilter(
        field_name="run__jobdef__project__suuid",
        method=filter_multiple,
        help_text="Filter run metrics on a project suuid or multiple project suuids via a comma seperated list.",
    )
    workspace_suuid = CharFilter(
        field_name="run__jobdef__project__workspace__suuid",
        method=filter_multiple,
        help_text="Filter run metrics on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )

    metric_name = CharFilter(field_name="metric__name")
    metric_value = CharFilter(field_name="metric__value")
    metric_type = CharFilter(field_name="metric__type")

    label_name = CharFilter(field_name="label__*__name", method=filter_array)
    label_value = CharFilter(field_name="label__*__value", method=filter_array)
    label_type = CharFilter(field_name="label__*__type", method=filter_array)


class RunMetricView(
    RunMetricObjectMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List metrics"""

    queryset = RunMetric.objects.all()
    max_page_size = 10000  # For metric listings we want to allow "a lot" of data in a single request
    search_fields = ["metric__name"]
    serializer_class = RunMetricSerializer
    ordering = "created_at"
    ordering_fields = [
        "created_at",
        "metric.name",
        "metric.value",
        "metric.type",
    ]

    filterset_class = RunMetricFilterSet

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


class RunMetricUpdateView(
    RunMetricObjectMixin,
    NestedViewSetMixin,
    UpdateModelWithoutPartialUpateMixin,
    viewsets.GenericViewSet,
):
    """Update the metrics for a run"""

    queryset = RunMetricMeta.objects.all()
    lookup_field = "run__suuid"
    serializer_class = RunMetricUpdateSerializer

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

    @extend_schema(responses={200: None})
    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        # TODO: change status code to 204 BUT also change CLI to handle 204
        return Response(None, status=200)

    def get_object_fallback(self):
        """Return a new RunMetric instance or raise 404 if Run does not exists."""
        run = get_object_or_404(Run.objects.active(), suuid=self.kwargs[self.lookup_field])

        run_metrics = RunMetricMeta.objects.create(run=run, metrics=[])
        run_metrics.metrics = []  # save initial data
        run_metrics.save()

        return run_metrics
