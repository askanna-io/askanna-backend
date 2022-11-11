import os

from core.permissions import RoleBasedPermission
from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
    ObjectRoleMixin,
    workspace_to_project_role,
)
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from run.models import ChunkedRunResultPart, Run, RunResult
from run.serializers import ChunkedRunResultPartSerializer, RunResultSerializer
from run.signals import result_upload_finish
from users.models import Membership


class BaseRunResultCreateView(
    ObjectRoleMixin,
    NestedViewSetMixin,
):
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "create": ["project.run.create"],
    }

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_object_workspace(self):
        return self.current_object.run.jobdef.project.workspace

    def get_create_role(self, request, *args, **kwargs):
        parents = self.get_parents_query_dict()
        try:
            run = Run.objects.get(suuid=parents.get("run__suuid"))
            project = run.jobdef.project
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


class RunResultCreateView(
    BaseRunResultCreateView,
    BaseUploadFinishMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Do a request to upload a new result"""

    queryset = RunResult.objects.filter(run__deleted__isnull=True)
    lookup_field = "suuid"
    serializer_class = RunResultSerializer

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = result_upload_finish
    upload_finished_message = "Job result uploaded"

    def get_upload_dir(self, obj):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", obj.run.suuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    # overwrite create row, we need to add the run
    def create(self, request, *args, **kwargs):
        run = Run.objects.get(suuid=self.kwargs.get("parent_lookup_run__suuid"))

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
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return "result_{}.output".format(obj.uuid.hex)

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["size"]
        instance_obj.size = resume_obj.size
        instance_obj.save(update_fields=update_fields)


class ChunkedJobResultViewSet(ObjectRoleMixin, BaseChunkedPartViewSet):
    """Request an uuid to upload a result chunk"""

    queryset = ChunkedRunResultPart.objects.all().select_related(
        "runresult__run__jobdef__project",
        "runresult__run__jobdef__project__workspace",
    )
    serializer_class = ChunkedRunResultPartSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "create": ["project.run.create"],
        "chunk": ["project.run.create"],
    }

    def initial(self, request, *args, **kwargs):
        """
        Set and lookup external relation by default
        """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        suuid = parents.get("runresult__suuid")
        request.data.update(
            **{
                "runresult": RunResult.objects.get(
                    suuid=suuid,
                ).pk
            }
        )

    def get_upload_dir(self, chunkpart):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", chunkpart.runresult.run.suuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.runresult.run.jobdef.project

    def get_object_workspace(self):
        return self.current_object.runresult.run.jobdef.project.workspace

    def get_create_role(self, request, *args, **kwargs):
        # The role for creating an artifact is based on the url it is accesing
        parents = self.get_parents_query_dict()
        try:
            runresult = RunResult.objects.get(suuid=parents.get("runresult__suuid"))
            project = runresult.run.jobdef.project
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
