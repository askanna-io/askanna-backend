import io
import json

import django_filters
from django.conf import settings
from django.db.models import Prefetch, Q
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE
from core.filters import filter_multiple
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.askanna import RoleBasedPermission
from core.viewsets import AskAnnaGenericViewSet
from job.models import JobDef, JobPayload, ScheduledJob
from job.serializers import JobSerializer, RequestJobRunSerializer
from package.models import Package
from run.models import Run
from run.serializers.run import RunStatusSerializer


class JobFilterSet(django_filters.FilterSet):
    project_suuid = django_filters.CharFilter(
        field_name="project__suuid",
        method=filter_multiple,
        help_text="Filter jobs on a project suuid or multiple project suuids via a comma seperated list.",
    )
    workspace_suuid = django_filters.CharFilter(
        field_name="project__workspace__suuid",
        method=filter_multiple,
        help_text="Filter jobs on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )


@extend_schema_view(
    list=extend_schema(description="List the jobs you have access to"),
    retrieve=extend_schema(description="Get info from a specific job"),
    partial_update=extend_schema(description="Update a job"),
    destroy=extend_schema(description="Remove a job"),
)
class JobView(
    ObjectRoleMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    queryset = (
        JobDef.objects.active()
        .select_related("project", "project__workspace")
        .prefetch_related(
            Prefetch("schedules", queryset=ScheduledJob.objects.order_by("next_run_at")),
            Prefetch(
                "project__packages",
                queryset=Package.objects.active().order_by("-created_at"),
            ),
        )
    )
    search_fields = ["suuid", "name"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "project.name",
        "project.suuid",
        "workspace.name",
        "workspace.suuid",
    ]
    ordering_fields_aliases = {
        "workspace.name": "project__workspace__name",
        "workspace.suuid": "project__workspace__suuid",
    }
    filterset_class = JobFilterSet

    serializer_class = JobSerializer

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.job.list"],
        "retrieve": ["project.job.list"],
        "destroy": ["project.job.remove"],
        "partial_update": ["project.job.edit"],
        "new_run": ["project.run.create"],
    }

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__pk__in=member_of_workspaces)
                | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        )

    def get_object_project(self):
        return self.current_object.project

    def perform_destroy(self, instance):
        instance.to_deleted()

    @extend_schema(
        description="Start a new run for a job",
        parameters=[
            OpenApiParameter("name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Name of the run"),
            OpenApiParameter(
                "description", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Description of the run"
            ),
        ],
        examples=[
            OpenApiExample(
                "JSON data payload",
                description="An example of an optional JSON data payload",
                value={"data": {"foo": "bar"}},
                request_only=True,
            ),
        ],
        request=RequestJobRunSerializer,
        responses={201: RunStatusSerializer},
    )
    @action(
        detail=True,
        methods=["post"],
        name="Request new job run",
        serializer_class=RequestJobRunSerializer,
        url_path="run/request/batch",
        queryset=JobDef.objects.active().select_related("project", "project__workspace"),
    )
    def new_run(self, request, suuid, **kwargs):
        job = self.get_object()
        payload = self.handle_payload(request=request, job=job)

        # Fetch the latest package found in the job.project
        package = Package.objects.active().filter(project=job.project).order_by("-created_at").first()

        run = Run.objects.create(
            name=request.query_params.get("name", ""),
            description=request.query_params.get("description", ""),
            jobdef=job,
            payload=payload,
            package=package,
            trigger=self.get_trigger_source(request),
            created_by_user=request.user,
        )

        # Return the run information
        serializer = RunStatusSerializer(run, context={"request": request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def handle_payload(self, request, job, **kwargs):
        """
        Asses incoming payload, it can be the case that there is no payload given and we don't create a payload
        """
        size = int(request.headers.get("content-length", 0))
        if size == 0:
            return None

        # Validate whether request.data is really a JSON structure
        try:
            assert isinstance(request.data, dict | list)
        except AssertionError as exc:
            raise ParseError(
                detail={
                    "payload": ["The JSON data payload is not valid, please check and try again"],
                },
            ) from exc

        # Create new JobPayload
        json_string = json.dumps(request.data)
        lines = 0
        try:
            lines = len(json.dumps(request.data, indent=1).splitlines())
        except Exception:  # nosec: B110
            pass

        job_payload = JobPayload.objects.create(jobdef=job, size=size, lines=lines, owner=request.user)
        job_payload.write(io.StringIO(json_string))

        return job_payload

    def get_trigger_source(self, request) -> str:
        """
        Determine the source of the API call by looking at the `askanna-agent` header.
        If this header is not set, we assume that the request is a regular API call.
        """
        source = request.headers.get("askanna-agent", "api").upper()
        # If the source is not in the allowed list, we know the API is used directly and we set the trigger to API
        return source if source in settings.ALLOWED_API_AGENTS else "API"
