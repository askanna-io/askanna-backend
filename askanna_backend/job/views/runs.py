# -*- coding: utf-8 -*-
import os
import re

from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.mixins import HybridUUIDMixin
from core.utils import get_config, is_valid_timezone
from core.views import PermissionByActionMixin, SerializerByActionMixin
from job.filters import RunFilter
from job.models import JobRun
from job.permissions import IsMemberOfJobDefAttributePermission
from job.serializers import JobRunSerializer, JobRunUpdateSerializer
from users.models import MSP_WORKSPACE


def string_expand_variables(strings: list, prefix: str = "PLV_") -> list:
    var_matcher = re.compile(r"\{\{ (?P<MYVAR>[\w\-]+) \}\}")
    for idx, line in enumerate(strings):
        matches = var_matcher.findall(line)
        for m in matches:
            line = line.replace("{{ " + m + " }}", "${" + prefix + m.strip() + "}")
        strings[idx] = line
    return strings


class JobRunView(
    PermissionByActionMixin,
    SerializerByActionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # we removed 'put' from the http_method_names as we don't support this in this view
    # - post and delete
    http_method_names = ["get", "patch", "head", "options", "trace"]

    queryset = JobRun.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobRunSerializer

    permission_classes = [
        IsMemberOfJobDefAttributePermission | IsAdminUser,
    ]

    permission_classes_by_action = {
        "update": [IsMemberOfJobDefAttributePermission | IsAdminUser],
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

    @action(
        detail=True,
        methods=["get"],
        name="JobRun Manifest",
    )
    def manifest(self, request, short_uuid, **kwargs):
        instance = self.get_object()
        jr = instance

        # What is the jobdef specified?
        jd = jr.jobdef
        pr = jd.project
        pl = jr.payload

        # FIXME: when versioning is in, point to version in JobRun
        package = jr.package

        # compose the path to the package in the project
        # This points to the blob location where the package is
        package_path = os.path.join(settings.BLOB_ROOT, str(package.uuid))

        # read config from askanna.yml
        config_file_path = os.path.join(package_path, "askanna.yml")
        if not os.path.exists(config_file_path):
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

        askanna_config = get_config(config_file_path)
        global_timezone = is_valid_timezone(
            askanna_config.get("timezone"), settings.TIME_ZONE
        )

        # see whether we are on the right job
        yaml_config = askanna_config.get(jd.name)
        if not yaml_config:
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

        job_commands = yaml_config.get("job")
        job_timezone = is_valid_timezone(yaml_config.get("timezone"), global_timezone)
        commands = []
        for command in job_commands:
            print_command = command.replace('"', '"')
            command = command.replace("{{ PAYLOAD_PATH }}", "$PAYLOAD_PATH")

            # also substitute variables we get from the PAYLOAD
            _command = string_expand_variables([command])
            command = _command[0]
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
                "TZ": job_timezone,
            },
        )

        return HttpResponse(entrypoint_string)

    @action(
        detail=True,
        methods=["get"],
        name="JobRun Log",
    )
    def log(self, request, short_uuid, **kwargs):
        instance = self.get_object()
        stdout = instance.output.stdout
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

        return Response(response_json)


class JobJobRunView(HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
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
        return queryset.filter(jobdef__project__workspace__in=member_of_workspaces)
