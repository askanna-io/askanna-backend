import json
import os
import uuid

from django.conf import settings
from drf_yasg import openapi

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ParseError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.mixins import HybridUUIDMixin
from job.models import JobDef, Job, get_job_pk, JobPayload, get_job, JobRun
from job.serializers import (
    JobSerializer,
    JobRunTestSerializer,
    StartJobSerializer,
    JobRunSerializer,
)


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
        # print(kwargs)
        # print(request.data)
        # print(request.POST)
        # print(request.user)
        # print(request.query_params)  # same as request.GET from django
        # print(request.FILES)

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
                    "detail": e,
                },
                status=400
            )

        # create new JobPayload
        job_pl = JobPayload.objects.create(
            jobdef=jobdef, storage_location="", owner=request.user
        )

        store_path = [
            settings.PROJECTS_ROOT,
            "payloads",
            jobdef.project.uuid.hex,
            job_pl.short_uuid,
        ]

        relative_storepath = [
            jobdef.project.uuid.hex,
            job_pl.short_uuid,
            "payload.json",
        ]

        job_pl.storage_location = os.path.join(*relative_storepath)
        job_pl.save()

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
                "next_url": "https://beta-api.askanna.io/v1/status/{}".format(
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
        # job = Job(pk=pk)
        # job = get_job(uuid)
        job = get_job(short_uuid)
        job.start()
        return Response({"status": "started"})

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

    @action(detail=True, methods=["get", "post"], name="Job Runs")
    def runs(self, request, short_uuid, pk=None, **kwargs):
        job = get_job(short_uuid)
        runs = JobRunTestSerializer(job.runs(), many=True)
        return Response(runs.data)

    @action(detail=True, methods=["post"], name="Job Status")
    def status(self, request, short_uuid, pk=None, **kwargs):
        job = get_job(short_uuid)
        return Response({"status": job.status()})


class JobRunView(viewsets.ModelViewSet):
    queryset = JobRun.objects.all()
    serializer_class = JobRunSerializer


class JobJobRunView(HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobRun.objects.all()
    serializer_class = JobRunSerializer


class ProjectJobViewSet(
    HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = JobDef.objects.all()
    serializer_class = JobSerializer

    # overwrite the default view and serializer for detail page
    # we want to use an other serializer for this.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs["context"] = self.get_serializer_context()
        serializer = JobSerializer(instance, **serializer_kwargs)
        return Response(serializer.data)
