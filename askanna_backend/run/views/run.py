import os

from core.permissions import ProjectMember, ProjectNoMember, RoleBasedPermission
from core.utils import stream
from core.views import (
    ObjectRoleMixin,
    SerializerByActionMixin,
    workspace_to_project_role,
)
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.template.loader import render_to_string
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from job.models import JobDef
from project.models import Project
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from run.filters import RunFilter
from run.models import RedisLogQueue, Run
from run.serializers import RunSerializer, RunUpdateSerializer
from users.models import MSP_WORKSPACE, Membership


class RunObjectRoleMixin:
    def get_object_project(self):
        return self.current_object.jobdef.project

    def get_object_workspace(self):
        return self.current_object.jobdef.project.workspace

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_create_role(self, request, *args, **kwargs):
        # The role for creating a Project is based on the payload
        # we read the 'workspace' suuid from the payload and determine the user role based on that
        project_suuid = None
        parents = self.get_parents_query_dict()
        project_suuid = parents.get("project__suuid") or request.data.get("project")
        try:
            project = Project.objects.get(suuid=project_suuid)
        except ObjectDoesNotExist:
            raise Http404

        workspace_role, request.membership = Membership.get_workspace_role(request.user, project.workspace)
        request.user_roles.append(workspace_role)
        request.object_role = workspace_role

        # try setting a project role based on workspace role
        if workspace_to_project_role(workspace_role) is not None:
            inherited_role = workspace_to_project_role(workspace_role)
            request.user_roles.append(inherited_role)

        return Membership.get_project_role(request.user, project)

    def get_workspace_role(self, user, *args, **kwargs):
        return Membership.get_workspace_role(user, self.current_object.jobdef.project.workspace)


@extend_schema_view(
    list=extend_schema(description="List the runs you have access to"),
    retrieve=extend_schema(description="Get info from a specific run"),
    update=extend_schema(description="Update a run"),
    partial_update=extend_schema(description="Update a run"),
    destroy=extend_schema(description="Remove a run"),
)
class RunView(
    RunObjectRoleMixin,
    ObjectRoleMixin,
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

    queryset = Run.objects.filter(deleted__isnull=True)
    lookup_field = "suuid"
    serializer_class = RunSerializer

    permission_classes = [RoleBasedPermission]
    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "log": ["project.run.list"],
        "manifest": ["project.run.list"],
        "result_download": ["project.run.list"],
        "create": ["project.run.create"],
        "destroy": ["project.run.remove"],
        "update": ["project.run.edit"],
        "partial_update": ["project.run.edit"],
    }

    serializer_classes_by_action = {
        "patch": RunUpdateSerializer,
    }

    filterset_class = RunFilter

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
                .select_related(
                    "jobdef",
                    "jobdef__project",
                    "jobdef__project__workspace",
                    "payload",
                    "payload__jobdef",
                    "payload__jobdef__project",
                    "package",
                    "created_by",
                    "member",
                    "output",
                )
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(jobdef__project__workspace__in=member_of_workspaces)
                | (Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
            )
            .select_related(
                "jobdef",
                "jobdef__project",
                "jobdef__project__workspace",
                "payload",
                "payload__jobdef",
                "payload__jobdef__project",
                "package",
                "created_by",
                "member",
                "output",
            )
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

    @action(
        detail=True,
        methods=["get"],
        name="Run Log",
    )
    def log(self, request, suuid, **kwargs):
        """Get the log from a specific run"""
        instance = self.get_object()
        if instance.is_finished:
            stdout = instance.output.stdout
        else:
            logqueue = RedisLogQueue(instance.suuid)
            stdout = logqueue.get()

        limit = request.query_params.get("limit", 100)
        offset = request.query_params.get("offset", 0)

        limit_or_offset = request.query_params.get("limit") or request.query_params.get("offset")
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
                response_json["next"] = "{scheme}://{host}{path}?limit={limit}&offset={offset}".format(
                    scheme=scheme,
                    limit=limit,
                    offset=offset + limit,
                    host=host,
                    path=path,
                )
            if offset - limit > -1:
                response_json["previous"] = "{scheme}://{host}{path}?limit={limit}&offset={offset}".format(
                    scheme=scheme,
                    limit=limit,
                    offset=offset - limit,
                    host=host,
                    path=path,
                )
            return Response(response_json, status=status.HTTP_206_PARTIAL_CONTENT)

        return Response(response_json)

    @action(
        detail=True,
        methods=["get", "head"],
        name="Run Result",
    )
    def result(self, request, suuid, **kwargs):
        """Get the result from a specific run"""
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

        return stream(request, run.result.stored_path, content_type=content_type, size=size)

    @action(
        detail=True,
        methods=["get"],
        name="Run Status",
    )
    def status(self, request, suuid, **kwargs):
        """Get the status from a specific run"""
        run = self.get_object()
        next_url = "{}://{}/v1/status/{}/".format(request.scheme, request.META["HTTP_HOST"], run.suuid)
        finished_next_url = "{}://{}/v1/result/{}/".format(request.scheme, request.META["HTTP_HOST"], run.suuid)

        base_status = {
            "message_type": "status",
            "suuid": run.suuid,
            "name": run.name,
            "created": run.created,
            "updated": run.modified,
            "duration": run.started and (timezone.now() - run.started).seconds or 0,
            "job": run.jobdef.relation_to_json,
            "project": run.jobdef.project.relation_to_json,
            "workspace": run.jobdef.project.workspace.relation_to_json,
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


class JobRunView(
    RunObjectRoleMixin,
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    """List all runs for a job"""

    queryset = Run.objects.filter(deleted__isnull=True)
    lookup_field = "suuid"
    serializer_class = RunSerializer
    permission_classes = [RoleBasedPermission]
    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
    }

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
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

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        job_suuid = kwargs.get("parent_lookup_jobdef__suuid")
        try:
            job = JobDef.objects.get(suuid=job_suuid)
        except ObjectDoesNotExist:
            raise Http404

        request.user_roles += Membership.get_roles_for_project(request.user, job.project)
        return Membership.get_project_role(request.user, job.project)
