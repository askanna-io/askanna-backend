# -*- coding: utf-8 -*-
import json
import io

from django.db.models import Q
from rest_framework import viewsets
from rest_framework.exceptions import ParseError
from rest_framework.response import Response

from core.const import ALLOWED_API_AGENTS
from core.permissions import RoleBasedPermission
from core.views import ObjectRoleMixin
from job.models import (
    JobDef,
    JobPayload,
    JobRun,
)
from job.serializers import StartJobSerializer
from package.models import Package
from users.models import MSP_WORKSPACE


class StartJobView(ObjectRoleMixin, viewsets.GenericViewSet):
    queryset = JobDef.jobs.active()
    lookup_field = "short_uuid"
    serializer_class = StartJobSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "newrun": ["project.run.create"],
    }

    def get_object_project(self):
        return self.current_object.project

    def get_object_workspace(self):
        return self.current_object.project.workspace

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        user = self.request.user
        if user.is_anonymous:
            # we don't allow anonymous users to start any jobs
            return super().get_queryset().none()

        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)

        # with the following query, when a project is set to PUBLIC,
        # or by workspace=PUBLIC
        # anyone can start a job except for people not logged in and
        # this is crusial as we need to register the "owner" of a run
        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__in=member_of_workspaces)
                | (
                    Q(project__workspace__visibility="PUBLIC")
                    & Q(project__visibility="PUBLIC")
                )
            )
        )

    def handle_payload(self, request, job, **kwargs):
        """
        Asses incoming payload, it can be the case that there is no payload given
        In that case, we don't create a payload
        """
        size = int(request.headers.get("content-length", 0))
        if size == 0:
            return None

        # validate whether request.data is really a json structure
        try:
            assert isinstance(
                request.data, (dict, list)
            ), "JSON not valid, please check and try again"
        except AssertionError as e:
            raise ParseError(
                detail={
                    "message_type": "error",
                    "message": "The JSON is not valid, please check and try again",
                    "detail": str(e),
                },
            )

        # create new JobPayload
        json_string = json.dumps(request.data)
        lines = 0
        try:
            lines = len(json.dumps(request.data, indent=1).splitlines())
        except Exception:
            pass

        job_pl = JobPayload.objects.create(
            jobdef=job, size=size, lines=lines, owner=request.user
        )
        job_pl.write(io.StringIO(json_string))

        return job_pl

    def get_trigger_source(self, request) -> str:
        """
        Determine the source of the API call by looking at the `askanna-agent` header.
        If this one is not set, we handle a regular API call
        """
        source = request.headers.get("askanna-agent", "api").upper()
        if source not in ALLOWED_API_AGENTS:
            # We don't actually block other parties to start a run, but set the agent to API
            return "API"
        return source

    def newrun(self, request, **kwargs):
        """
        We accept any data that is sent in request.data
        """
        job = self.get_object()
        payload = self.handle_payload(request=request, job=job)

        # TODO: Determine wheter we need the latest or pinned package
        # Fetch the latest package found in the job.project
        package = (
            Package.objects.filter(project=job.project).order_by("-created").first()
        )

        # create new Jobrun
        runspec = {
            "name": request.query_params.get("name"),
            "description": request.query_params.get("description"),
            "status": "PENDING",
            "jobdef": job,
            "payload": payload,
            "package": package,
            "trigger": self.get_trigger_source(request),
            "owner": request.user,
        }
        run = JobRun.objects.create(**runspec)

        # return the run id
        return Response(
            {
                "message_type": "status",
                "status": "queued",
                "uuid": run.uuid,
                "short_uuid": run.short_uuid,
                "name": run.name,
                "created": run.created,
                "updated": run.modified,
                "finished": None,
                "duration": 0,
                "job": run.jobdef.relation_to_json,
                "project": run.jobdef.project.relation_to_json,
                "workspace": run.jobdef.project.workspace.relation_to_json,
                "next_url": "{}://{}/v1/status/{}/".format(
                    request.scheme, request.META["HTTP_HOST"], run.short_uuid
                ),
            }
        )
