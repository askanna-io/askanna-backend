from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, Q, Value, When
from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters import FilterSet
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE
from core.filters import MultiUpperValueCharFilter, MultiValueCharFilter
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.role import RoleBasedPermission
from core.utils import stream
from run.models import RedisLogQueue
from run.models.run import STATUS_MAPPING, Run, get_status_external
from run.serializers.run import RunSerializer, RunStatusSerializer


class MultiRunStatusFilter(MultiValueCharFilter):
    def filter(self, qs, value):
        if not value:
            # No point filtering if empty
            return qs

        # Map "external" status values to internal values
        mapped_values = []
        for v in value:
            for key, val in STATUS_MAPPING.items():
                if val == v:
                    mapped_values.append(key)

        if not mapped_values:
            # There are no valid values, so return an empty queryset
            return qs.none()

        return super().filter(qs, mapped_values)


class RunFilterSet(FilterSet):
    run_suuid = MultiValueCharFilter(
        field_name="suuid",
        help_text="Filter runs on a run suuid. For multiple values, separate the values with commas.",
    )
    run_suuid__exclude = MultiValueCharFilter(
        field_name="suuid",
        exclude=True,
        help_text="Exclude runs on a run suuid. For multiple values, separate the values with commas.",
    )

    status = MultiRunStatusFilter(
        field_name="status",
        help_text=(
            "Filter runs on a status. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> queued, running, finished, failed"
        ),
    )
    status__exclude = MultiRunStatusFilter(
        field_name="status",
        exclude=True,
        help_text=(
            "Exclude runs on a status. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> queued, running, finished, failed"
        ),
    )

    trigger = MultiUpperValueCharFilter(
        field_name="trigger",
        help_text=(
            "Filter runs on a trigger. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> api, cli, python-sdk, webui, schedule, worker"
        ),
    )
    trigger__exclude = MultiUpperValueCharFilter(
        field_name="trigger",
        exclude=True,
        help_text=(
            "Exclude runs on a trigger. For multiple values, separate the values with commas."
            "</br><i>Available values:</i> api, cli, python-sdk, webui, schedule, worker"
        ),
    )

    job_suuid = MultiValueCharFilter(
        field_name="jobdef__suuid",
        help_text="Filter runs on a job suuid. For multiple values, separate the values with commas.",
    )
    job_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__suuid",
        exclude=True,
        help_text="Exclude runs on a job suuid. For multiple values, separate the values with commas.",
    )

    project_suuid = MultiValueCharFilter(
        field_name="jobdef__project__suuid",
        help_text="Filter runs on a project suuid. For multiple values, separate the values with commas.",
    )
    project_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__project__suuid",
        exclude=True,
        help_text="Exclude runs on a project suuid. For multiple values, separate the values with commas.",
    )

    workspace_suuid = MultiValueCharFilter(
        field_name="jobdef__project__workspace__suuid",
        help_text="Filter runs on a workspace suuid. For multiple values, separate the values with commas.",
    )
    workspace_suuid__exclude = MultiValueCharFilter(
        field_name="jobdef__project__workspace__suuid",
        exclude=True,
        help_text="Exclude runs on a workspace suuid. For multiple values, separate the values with commas.",
    )

    created_by_suuid = MultiValueCharFilter(
        field_name="created_by_member__suuid",
        help_text="Filter runs on a member suuid. For multiple values, separate the values with commas.",
    )
    created_by_suuid__exclude = MultiValueCharFilter(
        field_name="created_by_member__suuid",
        exclude=True,
        help_text="Exclude runs on a member suuid. For multiple values, separate the values with commas.",
    )

    package_suuid = MultiValueCharFilter(
        field_name="package__suuid",
        help_text="Filter runs on a package suuid. For multiple values, separate the values with commas.",
    )
    package_suuid__exclude = MultiValueCharFilter(
        field_name="package__suuid",
        exclude=True,
        help_text="Exclude runs on a package suuid. For multiple values, separate the values with commas.",
    )


@extend_schema_view(
    list=extend_schema(description="List the runs you have access to"),
    retrieve=extend_schema(description="Get info from a specific run"),
    update=extend_schema(description="Update a run"),
    partial_update=extend_schema(description="Update a run"),
    destroy=extend_schema(description="Remove a run"),
)
class RunView(
    ObjectRoleMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = (
        Run.objects.active()
        .select_related(
            "jobdef__project__workspace",
            "payload",
            "package",
            "created_by_member__user",
            "created_by_user",
            "run_image",
        )
        .prefetch_related(
            "result",
            "artifact",
            "output",
        )
        .annotate(
            member_name=Case(
                When(created_by_member__use_global_profile=True, then="created_by_user__name"),
                When(created_by_member__use_global_profile=False, then="created_by_member__name"),
            ),
            status_external=Case(
                When(status="SUBMITTED", then=Value(get_status_external("SUBMITTED"))),
                When(status="PENDING", then=Value(get_status_external("PENDING"))),
                When(status="PAUSED", then=Value(get_status_external("PAUSED"))),
                When(status="IN_PROGRESS", then=Value(get_status_external("IN_PROGRESS"))),
                When(status="FAILED", then=Value(get_status_external("FAILED"))),
                When(status="SUCCESS", then=Value(get_status_external("SUCCESS"))),
                When(status="COMPLETED", then=Value(get_status_external("COMPLETED"))),
            ),
        )
    )
    lookup_field = "suuid"
    search_fields = ["suuid", "name"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "job.name",
        "job.suuid",
        "project.name",
        "project.suuid",
        "workspace.name",
        "workspace.suuid",
        "created_by.name",
        "status",
    ]
    ordering_fields_aliases = {
        "job.name": "jobdef__name",
        "job.suuid": "jobdef__suuid",
        "project.name": "jobdef__project__name",
        "project.suuid": "jobdef__project__suuid",
        "workspace.name": "jobdef__project__workspace__name",
        "workspace.suuid": "jobdef__project__workspace__suuid",
        "created_by.name": "member_name",
        "status": "status_external",
    }
    filterset_class = RunFilterSet

    serializer_class = RunSerializer

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "log": ["project.run.list"],
        "manifest": ["project.run.list"],
        "result_download": ["project.run.list"],
        "create": ["project.run.create"],
        "destroy": ["project.run.remove"],
        "partial_update": ["project.run.edit"],
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
                .filter(Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(jobdef__project__workspace__in=member_of_workspaces)
                | (Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
            )
        )

    def get_object_project(self):
        return self.current_object.jobdef.project

    def perform_destroy(self, instance):
        instance.to_deleted()

    @extend_schema(responses={200: OpenApiTypes.BYTE})
    @action(detail=True, methods=["get"])
    def manifest(self, request, suuid, **kwargs):
        """Get the manifest for a specific run"""
        instance = self.get_object()
        jr = instance

        # What is the jobdef specified?
        jd = jr.jobdef
        pr = jd.project
        pl = jr.payload

        package = jr.package
        askanna_config = package.get_askanna_config()
        if askanna_config is None:
            # askanna.yml not found
            return HttpResponse(
                render_to_string(
                    "entrypoint_no_yaml.sh",
                    {
                        "pr": pr,
                        "jd": jd,
                    },
                )
            )

        # see whether we are on the right job
        job_config = askanna_config.jobs.get(jd.name)
        if not job_config:
            # {jd.name} is not specified in this askanna.yml, cannot start job
            return HttpResponse(
                render_to_string(
                    "entrypoint_job_notfound.sh",
                    {
                        "pr": pr,
                        "jd": jd,
                    },
                )
            )

        commands = []
        for command in job_config.commands:
            print_command = command.replace('"', '"')
            commands.append(
                {
                    "command": command,
                    "print_command": print_command,
                }
            )

        entrypoint_string = render_to_string(
            "entrypoint.sh",
            {
                "commands": commands,
                "pr": pr,
                "jd": jd,
                "jr": jr,
                "pl": pl,
            },
        )

        return HttpResponse(entrypoint_string)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "limit",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="Number of rows to return per request. To get all rows set limit to -1.<p><i>Default "
                "limit: 1000</i></p>",
            ),
            OpenApiParameter(
                "offset",
                OpenApiTypes.INT,
                OpenApiParameter.QUERY,
                description="The initial index from which to return the log.",
            ),
        ],
        request=None,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "count": {
                        "type": "integer",
                        "example": 123,
                    },
                    "next": {
                        "type": "string",
                        "nullable": True,
                        "format": "uri",
                        "example": "http://api.example.org/accounts/",
                    },
                    "previous": {
                        "type": "string",
                        "nullable": True,
                        "format": "uri",
                        "example": "http://api.example.org/accounts/",
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "example": [1, "2020-10-01T12:00:00.123456", "Preparing run environment"],
                        },
                    },
                },
            },
        },
    )
    @action(detail=True, methods=["get"], serializer_class=None)
    def log(self, request, suuid, **kwargs):
        "Get the log from a run"
        instance = self.get_object()
        if instance.is_finished:
            stdout = instance.output.stdout
        else:
            logqueue = RedisLogQueue(instance.suuid)
            stdout = logqueue.get()

        limit = int(request.query_params.get("limit", 10))
        offset = int(request.query_params.get("offset", 0))

        count = len(stdout) if stdout else 0

        response_json = {
            "count": count,
            "next": None,
            "previous": None,
            "results": None,
        }
        if limit == -1:
            response_json["results"] = stdout
        elif count:
            response_json["results"] = stdout[offset : offset + limit]

            scheme = request.scheme
            path = request.path
            host = request.META["HTTP_HOST"]
            if offset + limit < count:
                response_json["next"] = f"{scheme}://{host}{path}?limit={limit}&offset={offset + limit}"
            if offset - limit > -1:
                response_json["previous"] = f"{scheme}://{host}{path}?limit={limit}&offset={offset - limit}"

        return Response(response_json, status=status.HTTP_200_OK)

    @extend_schema(responses={200: OpenApiTypes.BYTE})
    @action(detail=True, methods=["get", "head"], serializer_class=None)
    def result(self, request, suuid, **kwargs):
        """Get the result from a specific run"""
        run = self.get_object()
        try:
            _ = run.result.uuid
        except ObjectDoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        if not Path.exists(run.result.stored_path):
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        # Get the requested content-type header, if not set get it from the result object
        content_type = request.headers.get("content-type", run.result.mime_type)
        size = run.result.size

        return stream(request, run.result.stored_path, content_type=content_type, size=size)

    @action(detail=True, methods=["get"], serializer_class=RunStatusSerializer)
    def status(self, request, suuid, **kwargs):
        """Get the status from a specific run"""
        run = self.get_object()
        serializer = RunStatusSerializer(run, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)
