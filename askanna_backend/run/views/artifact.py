import os

from core.mixins import ObjectRoleMixin
from core.permissions.role import RoleBasedPermission
from core.views import BaseChunkedPartViewSet, BaseUploadFinishViewSet
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
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


@extend_schema_view(
    list=extend_schema(description="List artifacts for a run"),
    create=extend_schema(
        description="Do a request to upload a new artifact",
        request=None,
        responses={201: RunArtifactSerializerForInsert},
    ),
    retrieve=extend_schema(description="Get info from a specific artifact"),
)
class RunArtifactView(
    ObjectRoleMixin,
    BaseUploadFinishViewSet,
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
    lookup_field = "suuid"
    serializer_class = RunArtifactSerializer

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "create": ["project.run.create"],
        "finish_upload": ["project.run.create"],
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "download": ["project.run.list"],
    }

    def get_upload_dir(self, obj):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", obj.run.suuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.run.jobdef.project

    def get_parrent_roles(self, request, *args, **kwargs):
        parents = self.get_parents_query_dict()
        try:
            run = Run.objects.get(suuid=parents.get("run__suuid"))
        except ObjectDoesNotExist:
            raise Http404

        return Membership.get_roles_for_project(request.user, run.jobdef.project)

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
        run = Run.objects.get(suuid=self.kwargs.get("parent_lookup_run__suuid"))
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
        """
        Get info to download an artifact

        The request returns a response with the URI on the CDN where to find the artifact file.
        """
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
    """Request an uuid to upload an artifact chunk"""

    queryset = ChunkedArtifactPart.objects.all()
    serializer_class = ChunkedRunArtifactPartSerializer

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "create": ["project.run.create"],
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "chunk": ["project.run.create"],
    }

    def get_upload_dir(self, chunkpart):
        # directory structure is containing the run-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "run", chunkpart.artifact.run.suuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.artifact.run.jobdef.project

    def get_parrent_roles(self, request, *args, **kwargs):
        parents = self.get_parents_query_dict()
        try:
            artifact = RunArtifact.objects.get(suuid=parents.get("artifact__suuid"))
        except ObjectDoesNotExist:
            raise Http404

        return Membership.get_roles_for_project(request.user, artifact.run.jobdef.project)

    def get_object(self):
        return self.get_object_without_permissioncheck()

    def initial(self, request, *args, **kwargs):
        """
        Set and lookup external relation by default
        """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        suuid = parents.get("artifact__suuid")
        request.data.update(
            **{
                "artifact": RunArtifact.objects.get(suuid=suuid).pk,
            }
        )
