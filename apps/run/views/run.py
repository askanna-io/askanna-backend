from django.db.models import Case, Q, Value, When
from django.http import HttpResponse
from django.template.loader import render_to_string
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE
from core.mixins import (
    ParserByActionMixin,
    PartialUpdateModelMixin,
    SerializerByActionMixin,
)
from core.permissions import AskAnnaPermissionByAction
from core.viewsets import AskAnnaGenericViewSet
from run.filters import RunFilterSet
from run.models.log import RedisLogQueue
from run.models.run import Run, get_status_external
from run.serializers.artifact import (
    RunArtifactCreateBaseSerializer,
    RunArtifactCreateWithFileSerializer,
    RunArtifactCreateWithoutFileSerializer,
)
from run.serializers.result import (
    RunResultCreateBaseSerializer,
    RunResultCreateWithFileSerializer,
    RunResultCreateWithoutFileSerializer,
)
from run.serializers.run import RunSerializer, RunStatusSerializer


@extend_schema_view(
    list=extend_schema(
        summary="List runs",
        description="List the runs you have access to",
    ),
    retrieve=extend_schema(
        summary="Get run info",
        description="Get info from a specific run",
    ),
    partial_update=extend_schema(
        summary="Update run info",
        description="Update the info of a specific run",
    ),
    destroy=extend_schema(
        summary="Remove a run",
        description="Remove a run",
    ),
    manifest=extend_schema(
        summary="Get run manifest",
    ),
    log=extend_schema(
        summary="Get run log",
    ),
    result=extend_schema(
        summary="Create a run result",
    ),
    artifact=extend_schema(
        summary="Create a new run artifact",
    ),
    status=extend_schema(
        summary="Get run status",
    ),
)
class RunView(
    ParserByActionMixin,
    SerializerByActionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    queryset = Run.objects.active(add_select_related=True).annotate(
        member_name=Case(
            When(created_by_member__use_global_profile=True, then="created_by_member__user__name"),
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

    permission_classes = [AskAnnaPermissionByAction]

    serializer_class = RunSerializer
    serializer_class_by_action = {
        "status": RunStatusSerializer,
    }

    parser_classes_by_action = {
        "artifact": [MultiPartParser, JSONParser],
        "result": [MultiPartParser, JSONParser],
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

    def perform_destroy(self, instance):
        instance.to_deleted()

    @extend_schema(responses={200: OpenApiTypes.BYTE})
    @action(detail=True, methods=["get"])
    def manifest(self, request, suuid, **kwargs):
        """Get the manifest for a specific run"""
        run = self.get_object()

        askanna_config = run.package.get_askanna_config()
        if askanna_config is None:
            return HttpResponse(
                render_to_string(
                    "entrypoint_no_yaml.sh",
                    {
                        "run": run,
                    },
                )
            )

        job_config = askanna_config.jobs.get(run.job.name)
        if not job_config:
            # The requested job is not specified in this askanna.yml, cannot start this job
            return HttpResponse(
                render_to_string(
                    "entrypoint_job_not_found.sh",
                    {
                        "run": run,
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

        return HttpResponse(
            render_to_string(
                "entrypoint.sh",
                {
                    "run": run,
                    "commands": commands,
                },
            )
        )

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
    def log(self, request, **kwargs):
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

    @extend_schema(
        request=RunResultCreateBaseSerializer,
        responses={
            status.HTTP_201_CREATED: PolymorphicProxySerializer(
                component_name="RunResultCreateSerializer",
                serializers=[RunResultCreateWithFileSerializer, RunResultCreateWithoutFileSerializer],
                resource_type_field_name=None,
                many=False,
            )
        },
    )
    @action(detail=True, methods=["post"])
    def result(self, request, **kwargs):
        """
        Do a request to upload a result for a run. At least a result file or filename is required.

        For large files it's recommended to use multipart upload. You can do this by providing a filename and NOT a
        result file. When you do such a request, in the response you will get upload info.

        If the upload info is of type `askanna` you can use the `upload_info.url` to upload file parts. By adding
        `part` to the url you can upload a file part. When all parts are uploaded you can do a request to complete
        the file by adding `complete` to the url. See the `storage` section in the API documentation for more info.

        By providing optional values for `size`, `etag` and `content_type` in the request body, the file will be
        validated against these values. If the values are not correct, the upload will fail.
        """

        run = self.get_object()
        if run.result:
            return Response({"detail": "Run already has a result"}, status=status.HTTP_400_BAD_REQUEST)

        if "result" not in request.FILES.keys() and "filename" not in request.data.keys():
            return Response({"detail": ("result or filename is required")}, status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class = (
            RunResultCreateWithFileSerializer if request.FILES.get("result") else RunResultCreateWithoutFileSerializer
        )

        context = self.get_serializer_context()
        context["run"] = run

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=RunArtifactCreateBaseSerializer,
        responses=PolymorphicProxySerializer(
            component_name="RunArtifactCreateSerializer",
            serializers=[RunArtifactCreateWithFileSerializer, RunArtifactCreateWithoutFileSerializer],
            resource_type_field_name=None,
            many=False,
        ),
    )
    @action(detail=True, methods=["post"])
    def artifact(self, request, **kwargs):
        """
        Do a request to upload an artifact for a run. At least an artifact file or filename is required.

        For large files it's recommended to use multipart upload. You can do this by providing a filename and NOT an
        artifact file. When you do such a request, in the response you will get upload info.

        If the upload info is of type `askanna` you can use the `upload_info.url` to upload file parts. By adding
        `part` to the url you can upload a file part. When all parts are uploaded you can do a request to complete
        the file by adding `complete` to the url. See the `storage` section in the API documentation for more info.

        By providing optional values for `size` and `etag` in the request body, the file will be validated against
        these values. If the values are not correct, the upload will fail.
        """

        run = self.get_object()

        if "artifact" not in request.FILES.keys() and "filename" not in request.data.keys():
            return Response({"detail": ("artifact or filename is required")}, status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class = (
            RunArtifactCreateWithFileSerializer
            if request.FILES.get("artifact")
            else RunArtifactCreateWithoutFileSerializer
        )

        context = self.get_serializer_context()
        context["run"] = run

        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def status(self, request, *args, **kwargs):
        """Get the status from a specific run"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
