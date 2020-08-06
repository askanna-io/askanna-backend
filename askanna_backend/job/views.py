import json
import os
import re
import uuid
import pprint

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import (
    StreamingHttpResponse,
    HttpResponse,
    HttpResponseRedirect,
    JsonResponse,
)
from django.template.loader import render_to_string
from drf_yasg import openapi

from rest_framework import mixins, viewsets
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from core.mixins import HybridUUIDMixin
from core.utils import get_config
from core.views import BaseChunkedPartViewSet, BaseUploadFinishMixin
from job.models import (
    JobDef,
    Job,
    get_job_pk,
    JobPayload,
    get_job,
    JobRun,
    JobArtifact,
    ChunkedArtifactPart,
    ChunkedJobOutputPart,
    JobOutput,
    JobVariable,
)
from job.serializers import (
    ChunkedArtifactPartSerializer,
    JobArtifactSerializer,
    JobArtifactSerializerForInsert,
    JobSerializer,
    StartJobSerializer,
    JobRunSerializer,
    JobPayloadSerializer,
    ChunkedJobOutputPartSerializer,
    JobOutputSerializer,
    JobVariableSerializer,
    JobVariableUpdateSerializer,
)
from job.signals import artifact_upload_finish, result_upload_finish
from package.models import Package
from users.models import Membership, MSP_WORKSPACE


class StartJobView(viewsets.GenericViewSet):
    queryset = JobDef.objects.all()
    lookup_field = "uuid"
    serializer_class = StartJobSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     query_val = self.kwargs.get("uuid", None)
    #     if query_val:
    #         print(query_val)
    #         return super().get_queryset()
    #     short_uuid = self.kwargs.get('short_uuid', None)
    #     print(short_uuid)
    #     return super().get_queryset().filter(short_uuid=short_uuid)

    def get_object(self):
        # TODO: move this to a mixin
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {}
        query_val = self.kwargs.get("uuid", None)
        if query_val:
            filter_kwargs = {"uuid": query_val}
        else:
            filter_kwargs = {"short_uuid": self.kwargs.get("short_uuid")}
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj

    def do_ingest_short(self, request, **kwargs):
        return self.do_ingest(request, **kwargs)

    def do_ingest(self, request, uuid=None, **kwargs):
        """
        We accept any data that is sent in request.data
        The provided `uuid` is really existing, as this is checked by the .get_object
        We specificed the `lookup_field` to search for uuid.
        """
        jobdef = self.get_object()

        # validate whether request.data is really a json structure
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
        except:
            pass

        job_pl = JobPayload.objects.create(
            jobdef=jobdef, size=size, lines=lines, owner=request.user
        )

        store_path = [settings.PAYLOADS_ROOT, job_pl.storage_location]

        # store incoming data as payload (in file format)
        os.makedirs(os.path.join(*store_path), exist_ok=True)
        with open(os.path.join(*store_path, "payload.json"), "w") as f:
            f.write(json_string)

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
                "run_uuid": jobrun.short_uuid,
                "created": jobrun.created,
                "updated": jobrun.modified,
                "next_url": "https://{}/v1/status/{}".format(
                    request.META["HTTP_HOST"], jobrun.short_uuid
                ),
            }
        )


class JobResultView(NestedViewSetMixin, viewsets.GenericViewSet):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     query_val = self.kwargs.get("uuid", None)
    #     if query_val:
    #         print(query_val)
    #         return super().get_queryset()
    #     short_uuid = self.kwargs.get('short_uuid', None)
    #     print(short_uuid)
    #     return super().get_queryset().filter(short_uuid=short_uuid)

    def get_object(self):
        # TODO: move this to a mixin
        queryset = self.filter_queryset(self.get_queryset())
        filter_kwargs = {}
        query_val = self.kwargs.get("uuid", None)
        if query_val:
            filter_kwargs = {"uuid": query_val}
        else:
            filter_kwargs = {"short_uuid": self.kwargs.get("short_uuid")}
        obj = get_object_or_404(queryset, **filter_kwargs)
        return obj

    def get_result(self, request, short_uuid, **kwargs):
        jobrun = self.get_object()
        return HttpResponse(jobrun.output.read, content_type="")

    def get_status(self, request, short_uuid, **kwargs):
        jobrun = self.get_object()
        next_url = "https://{}/v1/status/{}".format(
            request.META["HTTP_HOST"], jobrun.short_uuid
        )
        finished_next_url = "https://{}/v1/result/{}".format(
            request.META["HTTP_HOST"], jobrun.short_uuid
        )
        base_status = {
            "message_type": "status",
            "jobrun_uuid": jobrun.short_uuid,
            "created": jobrun.created,
            "updated": jobrun.modified,
            "next_url": next_url,
        }

        # translate the jobrun.status (celery) to our status
        status_trans = {
            "SUBMITTED": "queued",
            "PENDING": "queued",
            "PAUSED": "paused",
            "IN_PROGRESS": "running",
            "FAILED": "failed",
            "SUCCESS": "finished",
            "COMPLETED": "finished",
        }

        job_status = status_trans.get(jobrun.status, "unknown")
        base_status["status"] = job_status

        if job_status == "finished":
            base_status["next_url"] = finished_next_url
            base_status["finished"] = base_status["updated"]

        return Response(base_status)


class JobActionView(viewsets.ModelViewSet):
    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=["post"], name="Start job")
    def start(self, request, short_uuid, pk=None, **kwargs):
        """
        Based on the incoming short_uuid, we retrieve the JobDef
        Then we start and retrieve the JobRun for it.
        """
        job = get_job(short_uuid)
        jobrun = job.start()

        # return the JobRun id
        return Response(
            {
                "message_type": "status",
                "status": "queued",
                "run_uuid": jobrun.short_uuid,
                "created": jobrun.created,
                "updated": jobrun.modified,
                "next_url": "https://{}/v1/status/{}".format(
                    request.META["HTTP_HOST"], jobrun.short_uuid
                ),
            }
        )

    @action(detail=True, methods=["post"], name="Stop job")
    def stop(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        job.stop()
        return Response({"status": "stopped"})

    @action(detail=True, methods=["post"], name="Pause job")
    def pause(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        job.pause()
        return Response({"status": "paused"})

    @action(detail=True, methods=["post"], name="Reset job")
    def reset(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        job.stop()
        return Response({"status": "reset"})

    @action(detail=True, methods=["post"], name="Job info")
    def info(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        # return Response({'status': 'info'})
        return Response({"status": job.info()})

    @action(detail=True, methods=["post"], name="Kill job")
    def kill(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        job.kill()
        return Response({"status": "killed"})

    @action(detail=True, methods=["post"], name="Result job")
    def result(self, request, short_uuid, pk=None, **kwargs):
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        # job.result()
        return Response({"result": job.result()})

    @action(detail=True, methods=["post"], name="Job Status")
    def status(self, request, short_uuid, pk=None, **kwargs):
        job = get_job(short_uuid)
        return Response({"status": job.status()})


def string_expand_variables(strings: list, prefix: str = "PLV_") -> list:
    var_matcher = re.compile(r"\{\{ (?P<MYVAR>[\w\-]+) \}\}")
    for idx, line in enumerate(strings):
        matches = var_matcher.findall(line)
        for m in matches:
            line = line.replace("{{ " + m + " }}", "${" + prefix + m.strip() + "}")
        strings[idx] = line
    return strings


class JobRunView(viewsets.ModelViewSet):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    # FIXME: limit queryset to jobs the user can see, apply membership filter

    @action(detail=True, methods=["get"], name="JobRun Manifest")
    def manifest(self, request, short_uuid, **kwargs):
        # FIXME: only the jobrun.owner should be able to see this
        instance = self.get_object()
        jr = instance

        # What is the jobdef specified?
        jd = jr.jobdef
        pr = jd.project

        # FIXME: when versioning is in, point to version in JobRun
        package = jr.package

        # compose the path to the package in the project
        # This points to the blob location where the package is
        package_path = os.path.join(settings.BLOB_ROOT, str(package.uuid))

        # read config from askanna.yml
        config_file_path = os.path.join(package_path, "askanna.yml")
        if not os.path.exists(config_file_path):
            print("askanna.yml not found")
            return HttpResponse("")

        askanna_config = get_config(config_file_path)
        # see whether we are on the right job
        yaml_config = askanna_config.get(jd.name)
        if not yaml_config:
            print(f"{jd.name} is not specified in this askanna.yml, cannot start job")
            return HttpResponse("")

        job_commands = yaml_config.get("job")
        function_command = yaml_config.get("function")

        # we don't allow both function and job commands to be set
        if job_commands and function_command:
            print("cannot define both job and function")
            return HttpResponse("")

        commands = []
        for command in job_commands:
            print_command = command.replace('"', '"')
            command = command.replace("{{ PAYLOAD_PATH }}", "$PAYLOAD_PATH")

            # also substitute variables we get from the PAYLOAD
            _command = string_expand_variables([command])
            command = _command[0]
            commands.append({"command": command, "print_command": print_command})

        entrypoint_string = render_to_string(
            "entrypoint.sh", {"commands": commands, "pr": pr}
        )

        return HttpResponse(entrypoint_string)

    @action(detail=True, methods=["get"], name="JobRun Log")
    def log(self, request, short_uuid, **kwargs):
        instance = self.get_object()
        stdout = instance.output.stdout
        limit = request.query_params.get("limit", 100)
        offset = request.query_params.get("offset", 0)

        limit_or_offset = request.query_params.get("limit") or request.query_params.get(
            "offset"
        )
        count = len(stdout)

        response_json = stdout
        if limit_or_offset:
            offset = int(offset)
            limit = int(limit)
            response_json = {"count": count, "results": stdout[offset : offset + limit]}

            scheme = request.scheme
            path = request.path
            host = request.META["HTTP_HOST"]
            if offset + limit < count:
                response_json[
                    "next"
                ] = "{scheme}://{host}{path}?limit={limit}&offset={offset}".format(
                    scheme=scheme,
                    limit=limit,
                    offset=offset + limit,
                    host=host,
                    path=path,
                )
            if offset - limit > -1:
                response_json[
                    "previous"
                ] = "{scheme}://{host}{path}?limit={limit}&offset={offset}".format(
                    scheme=scheme,
                    limit=limit,
                    offset=offset - limit,
                    host=host,
                    path=path,
                )

        return Response(response_json)


class JobJobRunView(HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    # FIXME: limit queryset to jobs the user can see, apply membership filter


class JobPayloadView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobPayload.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobPayloadSerializer
    permission_classes = [IsAuthenticated]

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
            lines = json_obj[offset:limit]
            return HttpResponse("\n".join(lines), content_type="application/json")
        return JsonResponse(instance.payload)


class ProjectJobViewSet(
    HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    # overwrite the default view and serializer for detail page
    # we want to use an other serializer for this.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs["context"] = self.get_serializer_context()
        serializer = JobSerializer(instance, **serializer_kwargs)
        return Response(serializer.data)


class JobArtifactShortcutView(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet,
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
    permission_classes = [IsAuthenticated]

    # overwrite the default view and serializer for detail page
    # We will retrieve the artifact and send binary
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        artifact = instance.artifact.all().first()

        try:
            location = os.path.join(artifact.storage_location, artifact.filename)
            response = HttpResponseRedirect(
                "{scheme}://{ASKANNA_CDN_FQDN}/files/artifacts/{LOCATION}".format(
                    scheme=request.scheme,
                    ASKANNA_CDN_FQDN=settings.ASKANNA_CDN_FQDN,
                    LOCATION=location,
                )
            )
            return response
        except Exception as e:
            print(e)

        return Response(
            {"message_type": "error", "message": "Artifact was not found"}, status=404
        )


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
    permission_classes = [IsAuthenticated]

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = artifact_upload_finish
    upload_finished_message = "artifact upload finished"

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
        data.update(
            **{"jobrun": str(jobrun.pk),}
        )

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

        try:
            location = os.path.join(instance.storage_location, instance.filename)
            response = HttpResponseRedirect(
                "{scheme}://{ASKANNA_CDN_FQDN}/files/artifacts/{LOCATION}".format(
                    scheme=request.scheme,
                    ASKANNA_CDN_FQDN=settings.ASKANNA_CDN_FQDN,
                    LOCATION=location,
                )
            )
            return response
        except Exception as e:
            pass

        return Response(
            {"message_type": "error", "message": "Artifact was not found"}, status=404
        )


class ChunkedArtifactViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of artifacts
    """

    queryset = ChunkedArtifactPart.objects.all()
    serializer_class = ChunkedArtifactPartSerializer
    permission_classes = [IsAuthenticated]


class JobResultOutputView(
    BaseUploadFinishMixin, NestedViewSetMixin, viewsets.GenericViewSet,
):
    queryset = JobOutput.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobOutputSerializer
    permission_classes = [IsAuthenticated]

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = result_upload_finish
    upload_finished_message = "Job result uploaded"

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return "result_{}.output".format(obj.uuid.hex)

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    # def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
    #     update_fields = ["size"]
    #     instance_obj.size = resume_obj.size
    #     instance_obj.save(update_fields=update_fields)


class ChunkedJobOutputViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of jobresult
    """

    queryset = ChunkedJobOutputPart.objects.all()
    serializer_class = ChunkedJobOutputPartSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        joboutput = JobOutput.objects.get(
            short_uuid=self.kwargs.get("parent_lookup_joboutput__short_uuid")
        )
        data = request.data.copy()
        data.update(**{"joboutput": str(joboutput.pk)})

        serializer = ChunkedJobOutputPartSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )


class JobVariableView(
    NestedViewSetMixin,
    # mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobVariable.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobVariableSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Return different serializer class for update

        """
        if self.request.method.upper() in ["PUT", "PATCH"]:
            return JobVariableUpdateSerializer
        return self.serializer_class

    def get_queryset(self):
        """
        Return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return self.queryset.filter(project__workspace__in=member_of_workspaces)

