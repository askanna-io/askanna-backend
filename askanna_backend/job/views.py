import json
import os
import uuid

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.http import StreamingHttpResponse, HttpResponse
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
from core.views import BaseChunkedPartViewSet, BaseUploadFinishMixin
from job.models import JobDef, Job, get_job_pk, JobPayload, get_job, JobRun, JobArtifact, ChunkedArtifactPart
from job.serializers import (
    ChunkedArtifactPartSerializer,
    JobArtifactSerializer,
    JobArtifactSerializerForInsert,
    JobSerializer,
    StartJobSerializer,
    JobRunSerializer,
    JobPayloadSerializer,
)
from job.signals import artifact_upload_finish


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
        size = len(request.data)
        lines = 0
        try:
            lines = len(json.dumps(json.loads(request.data), indent=1).splitlines())
        except:
            pass

        job_pl = JobPayload.objects.create(
            jobdef=jobdef, 
            size=size,
            lines=lines,
            owner=request.user
        )

        store_path = [
            settings.PAYLOADS_ROOT,
            job_pl.storage_location
        ]

        # store incoming data as payload (in file format)
        os.makedirs(os.path.join(*store_path), exist_ok=True)
        with open(os.path.join(*store_path, "payload.json"), "w") as f:
            f.write(json.dumps(request.data))

        # create new Jobrun
        jobrun = JobRun.objects.create(jobdef=jobdef, payload=job_pl)

        # return the JobRun id
        return Response(
            {
                "message_type": "status",
                "status": "queued",
                "run_uuid": jobrun.short_uuid,
                "created": jobrun.created,
                "updated": jobrun.modified,
                "next_url": "https://{}/v1/status/{}".format(
                    request.META['HTTP_HOST'],
                    jobrun.short_uuid
                ),
            }
        )


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
                    request.META['HTTP_HOST'],
                    jobrun.short_uuid
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


class JobRunView(viewsets.ModelViewSet):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    # FIXME: limit queryset to jobs the user can see, apply membership filter

class JobJobRunView(HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
    permission_classes = [IsAuthenticated]

    # FIXME: limit queryset to jobs the user can see, apply membership filter

class JobPayloadView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobPayload.objects.all()
    serializer_class = JobPayloadSerializer
    permission_classes = [IsAuthenticated]

    # overwrite the default view and serializer for detail page
    # We will retrieve the original sent payload from the filesystem and serve as JSON
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance:
            return Response(instance.payload)

        return Response({
            "message_type": "error",
            "message": "Payload was not found"
        }, status=404)

    @action(detail=True, methods=["get"], name="Get partial payload")
    def get_partial(self, request, *args, **kwargs):
        """
        Slice the payload with offset+limit lines

        offset: defaults to 0
        limit: defaults to 500
        """
        offset = request.query_params.get('offset', 0)
        limit = request.query_params.get('limit', 500)

        instance = self.get_object()

        json_obj = json.dumps(instance.payload, indent=1).splitlines(keepends=False)
        lines = json_obj[offset:limit]
        return HttpResponse("\n".join(lines), content_type='application/json')


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

class JobArtifactView(BaseUploadFinishMixin, NestedViewSetMixin, 
                        mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    List all artifacts and allow to finish upload action
    """
    queryset = JobArtifact.objects.all()
    serializer_class = JobArtifactSerializer
    permission_classes = [IsAuthenticated]
    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = artifact_upload_finish
    upload_finished_message = "artifact upload finished"


    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        pass

    # overwrite create row, we need to add the jobrun
    def create(self, request, *args, **kwargs):
        jobrun = JobRun.objects.get(short_uuid=self.kwargs.get('parent_lookup_jobrun__short_uuid'))
        data = request.data.copy()
        data.update(**{
            'jobrun': str(jobrun.pk),
        })

        serializer = JobArtifactSerializerForInsert(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


    # overwrite the default view and serializer for detail page
    # We will retrieve the artifact and send binary
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        try:
            response = StreamingHttpResponse(instance.read, content_type="")
            response['Content-Disposition'] = "attachment; filename=artifact.zip"
            response['Content-Length'] = instance.size
        except Exception as e:
            pass
        else:
            return response

        return Response({
            "message_type": "error",
            "message": "Artifact was not found"
        }, status=404)


class ChunkedArtifactViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of artifacts
    """
    queryset = ChunkedArtifactPart.objects.all()
    serializer_class = ChunkedArtifactPartSerializer

    # overwrite create row, we need to add the jobrun
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.update(**{
            'artifact': self.kwargs.get('parent_lookup_artifact__uuid')
        })
        print(data)

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
