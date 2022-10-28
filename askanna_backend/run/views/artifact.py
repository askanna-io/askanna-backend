import os

from core.permissions import (
    ProjectMember,
    ProjectNoMember,
    PublicViewer,
    RoleBasedPermission,
)
from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
    ObjectRoleMixin,
    workspace_to_project_role,
)
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from run.models import ChunkedRunArtifactPart as ChunkedArtifactPart
from run.models import Run, RunArtifact
from run.serializers import (
    ChunkedRunArtifactPartSerializer,
    RunArtifactSerializer,
    RunArtifactSerializerDetail,
    RunArtifactSerializerForInsert,
)
from run.signals import artifact_upload_finish
from users.models import MSP_WORKSPACE, Membership


class RunArtifactShortcutView(
    ObjectRoleMixin,
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

    queryset = Run.objects.filter(deleted__isnull=True)
    lookup_field = "short_uuid"
    # The serializer class is dummy here as this is not used
    serializer_class = RunArtifactSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "retrieve": ["project.run.list"],
    }

    def get_object_project(self):
        return self.current_object.jobdef.project

    def get_object_workspace(self):
        return self.current_object.jobdef.project.workspace

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


class RunArtifactView(
    ObjectRoleMixin,
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

    queryset = RunArtifact.objects.all()
    lookup_field = "short_uuid"
    serializer_class = RunArtifactSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "create": ["project.run.create"],
        "finish_upload": ["project.run.create"],
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "download": ["project.run.list"],
    }

    def get_upload_dir(self, obj):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", obj.run.short_uuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_object_workspace(self):
        return self.current_object.run.jobdef.project.workspace

    def get_list_role(self, request, *args, **kwargs):
        return PublicViewer, None

    def get_create_role(self, request, *args, **kwargs):
        # The role for creating an artifact is based on the url it is accesing
        parents = self.get_parents_query_dict()
        try:
            run = Run.objects.get(short_uuid=parents.get("run__short_uuid"))
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

    upload_target_location = settings.ARTIFACTS_ROOT
    upload_finished_signal = artifact_upload_finish
    upload_finished_message = "artifact upload finished"

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
                .filter(
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(run__jobdef__project__workspace__in=member_of_workspaces)
                | (
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )
        )

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return obj.filename

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["size"]
        instance_obj.size = resume_obj.size
        instance_obj.save(update_fields=update_fields)

    # overwrite create row, we need to add the run
    def create(self, request, *args, **kwargs):
        run = Run.objects.get(short_uuid=self.kwargs.get("parent_lookup_run__short_uuid"))
        data = request.data.copy()
        data.update(**{"run": str(run.pk)})

        serializer = RunArtifactSerializerForInsert(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # overwrite the default view and serializer for detail page
    # We will retrieve the artifact and send binary
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs["context"] = self.get_serializer_context()
        serializer = RunArtifactSerializerDetail(instance, **serializer_kwargs)
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


class ChunkedArtifactViewSet(ObjectRoleMixin, BaseChunkedPartViewSet):
    """
    Allow chunked uploading of artifacts
    """

    queryset = ChunkedArtifactPart.objects.all()
    serializer_class = ChunkedRunArtifactPartSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "create": ["project.run.create"],
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "chunk": ["project.run.create"],
    }

    def get_upload_dir(self, chunkpart):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", chunkpart.artifact.run.short_uuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.artifact.run.jobdef.project

    def get_object_workspace(self):
        return self.current_object.artifact.run.jobdef.project.workspace

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_create_role(self, request, *args, **kwargs):
        # The role for creating an artifact is based on the url it is accesing
        parents = self.get_parents_query_dict()
        try:
            artifact = RunArtifact.objects.get(short_uuid=parents.get("artifact__short_uuid"))
            project = artifact.run.jobdef.project
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

    def get_object(self):
        return self.get_object_without_permissioncheck()

    def initial(self, request, *args, **kwargs):
        """
        Set and lookup external relation by default
        """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        short_uuid = parents.get("artifact__short_uuid")
        request.data.update(
            **{
                "artifact": RunArtifact.objects.get(short_uuid=short_uuid).pk,
            }
        )
