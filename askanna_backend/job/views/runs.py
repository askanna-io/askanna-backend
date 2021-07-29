# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import PermissionByActionMixin, SerializerByActionMixin
from job.filters import RunFilter
from job.models import JobRun, RedisLogQueue
from job.permissions import IsMemberOfJobDefAttributePermission
from job.serializers import JobRunSerializer, JobRunUpdateSerializer
from users.models import MSP_WORKSPACE


class JobRunView(
    PermissionByActionMixin,
    SerializerByActionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    # we removed 'put' from the http_method_names as we don't support this in this view
    # - post ( no run creation on this endpoint )
    http_method_names = ["get", "patch", "head", "options", "trace", "delete"]

    queryset = JobRun.objects.filter(deleted__isnull=True)
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer

    permission_classes = [
        IsMemberOfJobDefAttributePermission,
    ]

    permission_classes_by_action = {
        "update": [IsMemberOfJobDefAttributePermission],
    }

    serializer_classes_by_action = {
        "patch": JobRunUpdateSerializer,
    }

    filterset_class = RunFilter

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
            "jobdef",
            "jobdef__project",
            "payload",
            "payload__jobdef",
            "payload__jobdef__project",
            "package",
            "owner",
            "member",
            "output",
        )

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()

    @action(
        detail=True,
        methods=["get"],
        name="Run Manifest",
    )
    def manifest(self, request, short_uuid, **kwargs):
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

    @action(
        detail=True,
        methods=["get"],
        name="Run Log",
    )
    def log(self, request, short_uuid, **kwargs):
        instance = self.get_object()
        if instance.is_finished:
            stdout = instance.output.stdout
        else:
            logqueue = RedisLogQueue(instance.short_uuid)
            stdout = logqueue.get()

        limit = request.query_params.get("limit", 100)
        offset = request.query_params.get("offset", 0)

        limit_or_offset = request.query_params.get("limit") or request.query_params.get(
            "offset"
        )
        count = 0
        if stdout:
            count = len(stdout)

        response_json = stdout
        if limit_or_offset:
            offset = int(offset)
            limit = int(limit)
            results = []
            if count:
                # are we having lines?
                results = stdout[offset : offset + limit]
            response_json = {"count": count, "results": results}

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
            return Response(response_json, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response(response_json)


class JobJobRunView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobRun.objects.filter(deleted__isnull=True)
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
        return queryset.filter(jobdef__project__workspace__in=member_of_workspaces)
