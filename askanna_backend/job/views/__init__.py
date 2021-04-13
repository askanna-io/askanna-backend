# -*- coding: utf-8 -*-
import json
import io
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.mixins import HybridUUIDMixin
from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
    PermissionByActionMixin,
    SerializerByActionMixin,
)
from job.models import (
    ChunkedArtifactPart,
    JobArtifact,
    JobDef,
    JobPayload,
    JobRun,
    JobVariable,
)
from job.permissions import IsMemberOfProjectBasedOnPayload
from job.permissions import (
    IsMemberOfJobDefAttributePermission,
    IsMemberOfJobRunAttributePermission,
    IsMemberOfProjectAttributePermission,
)
from job.serializers import (
    ChunkedArtifactPartSerializer,
    JobArtifactSerializer,
    JobArtifactSerializerDetail,
    JobArtifactSerializerForInsert,
    JobPayloadSerializer,
    JobSerializer,
    JobVariableSerializer,
    JobVariableCreateSerializer,
    JobVariableUpdateSerializer,
    StartJobSerializer,
)
from job.signals import artifact_upload_finish
from package.models import Package
from users.models import MSP_WORKSPACE

from .metrics import RunMetricsRowView, RunMetricsView  # noqa: F401
from .result import (  # noqa: F401
    RunStatusView,
    RunResultView,
    RunOutputView,
    ChunkedJobOutputViewSet,
)
from .runs import JobRunView, JobJobRunView  # noqa: F401
from .runvariables import RunVariableRowView, RunVariablesView  # noqa: F401


class StartJobView(viewsets.GenericViewSet):
    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = StartJobSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

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
        return queryset.filter(project__workspace__in=member_of_workspaces)

    def do_ingest_short(self, request, **kwargs):
        return self.do_ingest(request, **kwargs)

    def do_ingest(self, request, uuid=None, **kwargs):
        """
        We accept any data that is sent in request.data
        """
        jobdef = self.get_object()

        # validate whether request.data is really a json structure
        # print(request.headers.items(), request.data)
        if "Content-Length" not in request.headers.keys():
            raise ParseError(detail="'Content-Length' HTTP-header is required")
        try:
            assert isinstance(
                request.data, dict
            ), "JSON not valid, please check and try again"
        except Exception as e:
            return Response(
                data={
                    "message_type": "error",
                    "message": "The JSON is not valid, please check and try again",
                    "detail": str(e),
                },
                status=400,
            )

        # create new JobPayload
        json_string = json.dumps(request.data)
        size = len(json_string)
        lines = 0
        try:
            lines = len(json.dumps(request.data, indent=1).splitlines())
        except Exception:
            pass

        job_pl = JobPayload.objects.create(
            jobdef=jobdef, size=size, lines=lines, owner=request.user
        )
        job_pl.write(io.StringIO(json_string))

        # FIXME: Determine wheter we need the latest or pinned package
        # Fetch the latest package found in the jobdef.project
        package = (
            Package.objects.filter(project=jobdef.project).order_by("-created").first()
        )

        # create new Jobrun
        jobrun = JobRun.objects.create(
            status="PENDING",
            jobdef=jobdef,
            payload=job_pl,
            package=package,
            owner=request.user,
        )

        # return the JobRun id
        return Response(
            {
                "message_type": "status",
                "status": "queued",
                "uuid": jobrun.uuid,
                "short_uuid": jobrun.short_uuid,
                "created": jobrun.created,
                "updated": jobrun.modified,
                "finished": None,
                "job": jobrun.jobdef.relation_to_json,
                "project": jobrun.jobdef.project.relation_to_json,
                "workspace": jobrun.jobdef.project.workspace.relation_to_json,
                "next_url": "{}://{}/v1/status/{}/".format(
                    request.scheme, request.META["HTTP_HOST"], jobrun.short_uuid
                ),
            }
        )


class JobActionView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

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
        return queryset.filter(project__workspace__in=member_of_workspaces)


class JobPayloadView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobPayload.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobPayloadSerializer
    permission_classes = [IsMemberOfJobDefAttributePermission]

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
        return queryset.filter(jobdef__project__workspace__in=member_of_workspaces)

    # overwrite the default view and serializer for detail page
    # We will retrieve the original sent payload from the filesystem and serve as JSON
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance:
            return Response(instance.payload)

        return Response(
            {"message_type": "error", "message": "Payload was not found"}, status=404
        )

    @action(detail=True, methods=["get"], name="Get partial payload")
    def get_partial(self, request, *args, **kwargs):
        """
        Slice the payload with offset+limit lines

        offset: defaults to 0
        limit: defaults to 500
        """
        offset = request.query_params.get("offset", 0)
        limit = request.query_params.get("limit", 500)

        instance = self.get_object()

        limit_or_offset = request.query_params.get("limit") or request.query_params.get(
            "offset"
        )
        if limit_or_offset:
            offset = int(offset)
            limit = int(limit)
            json_obj = json.dumps(instance.payload, indent=1).splitlines(keepends=False)
            lines = json_obj[offset : offset + limit]
            return HttpResponse("\n".join(lines), content_type="application/json")
        return JsonResponse(instance.payload)


class ProjectJobViewSet(
    HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    """
    This is a duplicated viewset like `JobActionView` but ReadOnly version
    """

    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

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
        return queryset.filter(project__workspace__in=member_of_workspaces)


class JobArtifactShortcutView(
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    Retrieve a specific artifact to be exposed over `/v1/artifact/{{ run_suuid }}`
    We allow the `run_suuid` to be given as short urls are for convenience to get
    something for a specific `run_suuid`.

    In case there is no artifact, we will return a http_status=404 (default via drf)

    In case we have 1 artifact, we return the binary of this artifact
    In case we find 1+ artifact, we return the first created artifact (sorted by date)
    """

    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    # The serializer class is dummy here as this is not used
    serializer_class = JobArtifactSerializer
    # FIXME: implement permission class that checks for access to this jobrun in workspace>project->job.
    permission_classes = [IsMemberOfJobDefAttributePermission]

    # overwrite the default view and serializer for detail page
    # We will retrieve the artifact and send binary
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            artifact = instance.artifact.all().first()
            location = os.path.join(artifact.storage_location, artifact.filename)
        except (ObjectDoesNotExist, AttributeError, Exception):
            return Response(
                {"message_type": "error", "message": "Artifact was not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:
            response = HttpResponseRedirect(
                "{BASE_URL}/files/artifacts/{LOCATION}".format(
                    BASE_URL=settings.ASKANNA_CDN_URL,
                    LOCATION=location,
                )
            )
            return response


class JobArtifactView(
    BaseUploadFinishMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List all artifacts and allow to finish upload action
    """

    queryset = JobArtifact.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobArtifactSerializer
    permission_classes = [IsMemberOfJobRunAttributePermission]

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = artifact_upload_finish
    upload_finished_message = "artifact upload finished"

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

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return obj.filename

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["size"]
        instance_obj.size = resume_obj.size
        instance_obj.save(update_fields=update_fields)

    # overwrite create row, we need to add the jobrun
    def create(self, request, *args, **kwargs):
        jobrun = JobRun.objects.get(
            short_uuid=self.kwargs.get("parent_lookup_jobrun__short_uuid")
        )
        data = request.data.copy()
        data.update(**{"jobrun": str(jobrun.pk)})

        serializer = JobArtifactSerializerForInsert(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    # overwrite the default view and serializer for detail page
    # We will retrieve the artifact and send binary
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs["context"] = self.get_serializer_context()
        serializer = JobArtifactSerializerDetail(instance, **serializer_kwargs)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download(self, request, *args, **kwargs):
        instance = self.get_object()

        return Response(
            {
                "action": "redirect",
                "target": "{BASE_URL}/files/artifacts/{LOCATION}".format(
                    BASE_URL=settings.ASKANNA_CDN_URL,
                    LOCATION="/".join([instance.storage_location, instance.filename]),
                ),
            }
        )


class ChunkedArtifactViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of artifacts
    """

    queryset = ChunkedArtifactPart.objects.all()
    serializer_class = ChunkedArtifactPartSerializer
    # FIXME: implement permission class that checks for access to this chunk in workspace>project->jobartifact.
    permission_classes = [IsAuthenticated]


class JobVariableView(
    PermissionByActionMixin,
    SerializerByActionMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobVariable.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobVariableSerializer

    filter_backends = (OrderingFilter, DjangoFilterBackend)
    ordering = ["project__name", "name"]
    ordering_fields = ["name", "project__name"]

    permission_classes = [
        IsAuthenticated,
    ]

    permission_classes_by_action = {
        "list": [IsAuthenticated | IsAdminUser],
        "create": [IsAuthenticated, IsMemberOfProjectBasedOnPayload | IsAdminUser],
        "update": [IsAuthenticated, IsMemberOfProjectBasedOnPayload | IsAdminUser],
        "partial_update": [
            IsAuthenticated,
            IsMemberOfProjectBasedOnPayload | IsAdminUser,
        ],
    }

    serializer_classes_by_action = {
        "post": JobVariableCreateSerializer,
        "put": JobVariableUpdateSerializer,
        "patch": JobVariableUpdateSerializer,
    }

    def initial(self, request, *args, **kwargs):
        """
        Set default request.data in case we need this
        """
        project_suuid = None
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        if self.request.method.upper() in ["PUT", "PATCH"]:
            if hasattr(request.data, "_mutable"):
                setattr(request.data, "_mutable", True)
            if parents.get("project__short_uuid"):
                project_suuid = parents.get("project__short_uuid")
                request.data.update({"project": project_suuid})

            if not project_suuid:
                """
                Determine the project id by getting it from the object requested
                """
                variable = self.get_object()
                project_suuid = variable.project.short_uuid
                request.data.update({"project": project_suuid})

            if hasattr(request.data, "_mutable"):
                setattr(request.data, "_mutable", False)

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
        return queryset.filter(project__workspace__in=member_of_workspaces)
