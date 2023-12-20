from django.db.models import Q
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE
from core.mixins import (
    ParserByActionMixin,
    PartialUpdateModelMixin,
    SerializerByActionMixin,
)
from core.permissions.askanna import AskAnnaPermissionByAction
from core.viewsets import AskAnnaGenericViewSet
from project.models import Project
from run.models import Run, RunArtifact
from run.serializers.artifact import (
    RunArtifactCreateBaseSerializer,
    RunArtifactCreateWithFileSerializer,
    RunArtifactCreateWithoutFileSerializer,
    RunArtifactSerializer,
    RunArtifactSerializerWithFileList,
)


@extend_schema_view(
    create=extend_schema(
        summary="Create a new run artifact",
        request=RunArtifactCreateBaseSerializer,
        responses=PolymorphicProxySerializer(
            component_name="RunArtifactCreateSerializer",
            serializers=[RunArtifactCreateWithFileSerializer, RunArtifactCreateWithoutFileSerializer],
            resource_type_field_name=None,
            many=False,
        ),
    ),
    retrieve=extend_schema(
        summary="Get run artifact info",
        description=(
            "Retrieve information about a run artifact. This includes the artifact meta data, download info and a "
            "list of files that are part of the artifact."
        ),
    ),
    partial_update=extend_schema(
        summary="Update run artifact info",
        description="Update the run artifact's `description`.",
    ),
)
class RunArtifactView(
    ParserByActionMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    AskAnnaGenericViewSet,
):
    """
    Retrieve information about a run's artifact and update the artifact's info.

    Note: creating a run artifact and retrieving a list of run artifacts is implemented in the `RunView`.
    """

    queryset = RunArtifact.objects.active(add_select_related=True)

    permission_classes = [AskAnnaPermissionByAction]

    serializer_class = RunArtifactSerializer
    serializer_class_by_action = {
        "list": RunArtifactSerializer,
        "retrieve": RunArtifactSerializerWithFileList,
        "partial_update": RunArtifactSerializerWithFileList,
    }

    parser_classes_by_action = {
        "create": [MultiPartParser, JSONParser],
    }

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        if self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )

        member_of_workspaces = self.request.user.memberships.filter(object_type=MSP_WORKSPACE).values_list(
            "object_uuid", flat=True
        )

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

    def get_parrent_project(self, request) -> Project:
        """
        Creating a run artifact is linked to the permissions of the run's project. To get the project we need to get
        the run_suuid from the payload and provide the object to the permission class.

        You can only create a run artifact if you have the permission to create an artifact on the run's project, so
        you need to be authenticated with an account that has a membership with matching permissions.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            run_suuid = request.data.get("run_suuid")
            if not run_suuid:
                raise ValidationError({"run_suuid": ["This field is required."]})

            try:
                return Run.objects.active(add_select_related=True).get(suuid=run_suuid).jobdef.project
            except Run.DoesNotExist:
                raise NotFound from None

        raise NotImplementedError(
            f"get_parrent_project is not implemented for class '{self.__class__.__name__}' and action '{self.action}'"
        )

    def create(self, request, *args, **kwargs):
        """
        Do a request to upload an artifact for a run. At least an artifact file or filename is required.

        For large files it's recommended to use multipart upload. You can do this by providing a filename and NOT an
        artifact file. When you do such a request, in the response you will get upload info.

        If the upload info is of type `askanna` you can use the `upload_info.url` to upload file parts. By adding
        `part` to the url you can upload a file part. When all parts are uploaded you can do a request to complete
        the file by adding `complete` to the url. See the `storage` section in the API documentation for more info.

        By providing optional values for `size` and `etag` in the request body, the file will be validated against
        these values. If the values are not correct, the upload will fail.
        """
        if "artifact" not in request.FILES.keys() and "filename" not in request.data.keys():
            return Response({"detail": ("artifact or filename is required")}, status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class = (
            RunArtifactCreateWithFileSerializer
            if request.FILES.get("artifact")
            else RunArtifactCreateWithoutFileSerializer
        )

        return super().create(request, *args, **kwargs)
