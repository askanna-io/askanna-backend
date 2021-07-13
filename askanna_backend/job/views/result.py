# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from rest_framework import status, viewsets, mixins
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
)
from job.models import (
    JobRun,
    RunResult,
    ChunkedRunResultPart,
)
from job.permissions import (
    IsMemberOfJobDefAttributePermission,
    IsMemberOfRunResultAttributePermission,
    IsMemberOfRunAttributePermission,
)
from job.serializers import (
    JobRunSerializer,
    RunResultSerializer,
    ChunkedRunResultPartSerializer,
)
from job.signals import result_upload_finish
from job.utils import stream
from users.models import MSP_WORKSPACE


class BaseRunResultView(
    NestedViewSetMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer
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
        return queryset.filter(
            jobdef__project__workspace__in=member_of_workspaces
        ).select_related(
            "package",
            "payload",
            "payload__jobdef__project",
            "jobdef",
            "jobdef__project",
            "owner",
            "member",
        )


class RunResultView(BaseRunResultView):
    def retrieve(self, request, short_uuid, *args, **kwargs):
        run = self.get_object()
        try:
            run.result.uuid
        except ObjectDoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        # get the requested content-type header, if not set from database
        content_type = request.headers.get("content-type", run.result.mime_type)
        size = run.result.size

        if not os.path.exists(run.result.stored_path):
            # the output file doesn't exist, return blank
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        return stream(
            request, run.result.stored_path, content_type=content_type, size=size
        )

    def options(self, request, *args, **kwargs):
        """
        Handler method for HTTP 'OPTIONS' request.
        """
        run = self.get_object()

        try:
            run.result.uuid
        except ObjectDoesNotExist:
            return Response(None, status=status.HTTP_404_NOT_FOUND)

        content_type = run.result.mime_type
        resp = Response(
            "",
            status=status.HTTP_200_OK,
            content_type=content_type,
        )
        resp["Content-Length"] = run.result.size
        resp["Accept-Ranges"] = "bytes"
        return resp


class RunStatusView(BaseRunResultView):
    def get_environment(self, instance):
        environment = {
            "name": instance.environment_name,
            "description": None,
            "label": None,
            "image": None,
            "timezone": instance.timezone,
        }
        if instance.run_image:
            environment["image"] = {
                "name": instance.run_image.name,
                "tag": instance.run_image.tag,
                "digest": instance.run_image.digest,
            }
        return environment

    def retrieve(self, request, short_uuid, *args, **kwargs):
        run = self.get_object()
        next_url = "{}://{}/v1/status/{}/".format(
            request.scheme, request.META["HTTP_HOST"], run.short_uuid
        )
        finished_next_url = "{}://{}/v1/result/{}/".format(
            request.scheme, request.META["HTTP_HOST"], run.short_uuid
        )
        base_status = {
            "message_type": "status",
            "uuid": run.uuid,
            "short_uuid": run.short_uuid,
            "name": run.name,
            "created": run.created,
            "updated": run.modified,
            "duration": run.started and (timezone.now() - run.started).seconds or 0,
            "job": run.jobdef.relation_to_json,
            "project": run.jobdef.project.relation_to_json,
            "workspace": run.jobdef.project.workspace.relation_to_json,
            "environment": self.get_environment(run),
            "next_url": next_url,
        }

        # translate the run.status (celery) to our status
        status_trans = {
            "SUBMITTED": "queued",
            "PENDING": "queued",
            "PAUSED": "paused",
            "IN_PROGRESS": "running",
            "FAILED": "failed",
            "SUCCESS": "finished",
            "COMPLETED": "finished",
        }

        job_status = status_trans.get(run.status, "unknown")
        base_status["status"] = job_status

        if run.is_finished:
            base_status["next_url"] = finished_next_url
            base_status["finished"] = run.finished
            base_status["duration"] = run.duration

        return Response(base_status)


class RunResultCreateView(
    BaseUploadFinishMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = RunResult.objects.all()
    lookup_field = "short_uuid"
    serializer_class = RunResultSerializer
    permission_classes = [IsMemberOfRunAttributePermission]

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = result_upload_finish
    upload_finished_message = "Job result uploaded"

    # overwrite create row, we need to add the jobrun
    def create(self, request, *args, **kwargs):
        run = JobRun.objects.get(
            short_uuid=self.kwargs.get("parent_lookup_run__short_uuid")
        )

        data = request.data.copy()
        data.update(
            **{
                "name": data.get("filename"),
                "job": str(run.jobdef.pk),
                "run": str(run.pk),
                "owner": str(request.user.uuid),
            }
        )
        serializer = RunResultSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return "result_{}.output".format(obj.uuid.hex)

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["lines", "size"]
        instance_obj.lines = len(instance_obj.read.splitlines())
        instance_obj.size = resume_obj.size
        instance_obj.save(update_fields=update_fields)


class ChunkedJobResultViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of jobresult
    """

    queryset = ChunkedRunResultPart.objects.all()
    serializer_class = ChunkedRunResultPartSerializer
    permission_classes = [IsMemberOfRunResultAttributePermission]

    def initial(self, request, *args, **kwargs):
        """
        Set and lookup external relation by default
        """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        short_uuid = parents.get("runresult__short_uuid")
        request.data.update(
            **{
                "runresult": RunResult.objects.get(
                    short_uuid=short_uuid,
                ).pk
            }
        )
