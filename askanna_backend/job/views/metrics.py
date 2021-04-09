# -*- coding: utf-8 -*-

from django.http.response import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import PermissionByActionMixin
from job.models import RunMetrics, RunMetricsRow
from job.filters import MetricFilter
from job.permissions import (
    IsMemberOfJobDefAttributePermission,
    IsMemberOfJobRunAttributePermission,
)
from job.serializers import RunMetricsRowSerializer, RunMetricsSerializer
from project.models import Project
from users.models import MSP_WORKSPACE


class RunMetricsRowView(
    PermissionByActionMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = RunMetricsRow.objects.all().order_by("created")
    lookup_field = "run_suuid"  # not needed for listviews
    serializer_class = RunMetricsRowSerializer

    # Override default, remove OrderingFilter because we use the DjangoFilterBackend version
    filter_backends = (DjangoFilterBackend,)

    filterset_class = MetricFilter
    permission_classes = [
        IsMemberOfJobRunAttributePermission | IsAdminUser,
    ]

    permission_classes_by_action = {
        "list": [IsMemberOfJobRunAttributePermission | IsAdminUser],
        "create": [IsMemberOfJobRunAttributePermission | IsAdminUser],
        "update": [IsMemberOfJobRunAttributePermission | IsAdminUser],
    }

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        member_of_projects = Project.objects.filter(
            workspace_id__in=member_of_workspaces
        ).values_list("short_uuid", flat=True)[
            ::-1
        ]  # hard convert to list for cross db query
        return queryset.filter(project_suuid__in=member_of_projects)


class RunMetricsView(
    PermissionByActionMixin,
    NestedViewSetMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):

    # we removed 'patch' from the http_method_names as we don't suppor this in this view
    # - post and delete
    http_method_names = ["get", "put", "head", "options", "trace"]

    queryset = RunMetrics.objects.all()
    lookup_field = "jobrun__short_uuid"
    serializer_class = RunMetricsSerializer

    permission_classes = [
        IsMemberOfJobRunAttributePermission | IsAdminUser,
    ]

    permission_classes_by_action = {
        "update": [IsMemberOfJobRunAttributePermission | IsAdminUser],
    }

    @action(detail=True, methods=["get"])
    def meta(self, request, *args, **kwargs):
        instance = self.get_object()
        return Response(
            {
                "suuid": instance.short_uuid,
                "project": instance.jobrun.jobdef.project.relation_to_json,
                "workspace": instance.jobrun.jobdef.project.workspace.relation_to_json,
                "job": instance.jobrun.jobdef.relation_to_json,
                "run": instance.jobrun.relation_to_json,
                "size": instance.size,
                "count": instance.count,
                "labels": instance.jobrun.metric_labels,
                "created": instance.created,
                "modified": instance.modified,
            }
        )

    # Override because we don't return the full object, just the `metrics` field
    def update(self, request, *args, **kwargs):
        _ = kwargs.pop("partial", False)
        instance = self.get_object()
        instance.metrics = request.data.get("metrics", [])
        instance.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        instance.refresh_from_db()
        return Response(instance.metrics)

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return queryset.filter(
            jobrun__jobdef__project__workspace__in=member_of_workspaces
        )

    def get_parent_instance(self):
        Model = self.get_queryset().model
        # Get parent instance.
        parent_queryset = Model.jobrun.field.related_model.objects
        filter_kwargs = {"short_uuid": self.kwargs[self.lookup_field]}
        parent = get_object_or_404(parent_queryset, **filter_kwargs)
        return parent

    def new_object(self):
        """Return a new RunMetrics instance or raise 404 if Run does not exists."""
        # Do not use direct Class to avoid hardcoded dependencies.
        Model = self.get_queryset().model
        parent = self.get_parent_instance()
        # Generate the new instance.
        run_metrics = Model(jobrun=parent)

        # May raise a permission denied
        self.check_object_permissions(self.request, run_metrics)
        return run_metrics

    def get_object(self):
        """Return the RunMetrics instance for the JobRun with the given id or 404."""
        try:
            return super().get_object()
        except Http404:
            """
            Here the metrics object doesn't exist yet, but we only create one if
            it is a member of the workspace, so check permissions towards the run object
            """

            # First try to see the parent exist
            parent = self.get_parent_instance()
            for permission in [IsMemberOfJobDefAttributePermission()]:
                if not permission.has_object_permission(
                    request=self.request, view=self, obj=parent
                ):
                    self.permission_denied(
                        self.request, message=getattr(permission, "message", None)
                    )

            return self.new_object()
