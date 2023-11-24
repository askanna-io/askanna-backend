import django_filters
from django.db.models import Case, Q, When
from drf_spectacular.utils import (
    PolymorphicProxySerializer,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, status
from rest_framework.exceptions import NotAuthenticated, NotFound, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE
from core.filters import filter_multiple
from core.mixins import PartialUpdateModelMixin
from core.permissions.askanna import AskAnnaPermissionByAction
from core.viewsets import AskAnnaGenericViewSet
from package.models import Package
from package.serializers import (
    PackageCreateBaseSerializer,
    PackageCreateWithFileSerializer,
    PackageCreateWithoutFileSerializer,
    PackageSerializer,
    PackageSerializerWithFileList,
)
from project.models import Project


class PackageFilterSet(django_filters.FilterSet):
    project_suuid = django_filters.CharFilter(
        field_name="project__suuid",
        method=filter_multiple,
        help_text="Filter packages on a project suuid or multiple project suuids via a comma seperated list.",
    )
    workspace_suuid = django_filters.CharFilter(
        field_name="project__workspace__suuid",
        method=filter_multiple,
        help_text="Filter packages on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )
    created_by_suuid = django_filters.CharFilter(
        field_name="created_by_member__suuid",
        method=filter_multiple,
        help_text="Filter packages on a created by suuid or multiple created by suuids via a comma seperated list.",
    )
    created_by_name = django_filters.CharFilter(
        field_name="member_name",
        lookup_expr="icontains",
        help_text="Filter packages on a created by name.",
    )


@extend_schema_view(
    create=extend_schema(
        summary="Create a new package",
        request=PackageCreateBaseSerializer,
        responses=PolymorphicProxySerializer(
            component_name="PackageCreateSerializer",
            serializers=[PackageCreateWithFileSerializer, PackageCreateWithoutFileSerializer],
            resource_type_field_name=None,
            many=False,
        ),
    ),
    list=extend_schema(
        summary="List packages",
        description=(
            "List all packages for a project for which you have access to. The list is paginated and you can use "
            "ordering, search and fields to filter the list."
        ),
    ),
    retrieve=extend_schema(
        summary="Get package info",
        responses=PackageSerializerWithFileList,
    ),
    partial_update=extend_schema(
        summary="Update package info",
        description="Update the package's `description`.",
        request=PackageSerializer,
        responses=PackageSerializer,
    ),
    destroy=extend_schema(
        summary="Remove a package",
        description=(
            "Remove a package from a project."
            "<p><strong>Warning:</strong> this action also deletes runs performed with the removed package.</p>"
        ),
    ),
)
class PackageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    """
    List all packages, create new packages, update package info and remove packages for a project.
    """

    queryset = Package.objects.active(add_select_related=True).annotate(
        created_by_name=Case(
            When(
                package_file___created_by__account_membership__use_global_profile=True,
                then="package_file___created_by__account_membership__user__name",
            ),
            When(
                package_file___created_by__account_membership__use_global_profile=False,
                then="package_file___created_by__account_membership__name",
            ),
        ),
    )

    search_fields = ["suuid", "package_file__name"]
    ordering_fields = [
        "filename",
        "created_at",
        "modified_at",
        "project.name",
        "project.suuid",
        "workspace.name",
        "workspace.suuid",
        "created_by.name",
    ]
    ordering_fields_aliases = {
        "filename": "package_file__name",
        "workspace.name": "project__workspace__name",
        "workspace.suuid": "project__workspace__suuid",
        "created_by.name": "created_by_name",
    }
    filterset_class = PackageFilterSet
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    serializer_class = PackageSerializer
    permission_classes = [AskAnnaPermissionByAction]

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        if self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )

        member_of_workspaces = self.request.user.active_memberships.filter(object_type=MSP_WORKSPACE).values_list(
            "object_uuid", flat=True
        )

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__pk__in=member_of_workspaces)
                | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        )

    def get_parrent_project(self, request) -> Project | None:
        """
        Creating a package is linked to the permissions of the project. To get the project we need to get the
        project_suuid from the payload and provide the object to the permission class.

        You can only create a package if you have the permission to create a package on the project, so you need
        to be authenticated with an account that has a membership with matching permissions.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            project_suuid = request.data.get("project_suuid")
            if not project_suuid:
                raise ValidationError({"project_suuid": ["This field is required."]})

            try:
                return Project.objects.active(add_select_related=True).get(suuid=project_suuid)
            except Project.DoesNotExist:
                raise NotFound from None

        return None

    def create(self, request, *args, **kwargs):
        """
        Do a request to upload a new package to a project for which you have access to. At least a package or filename
        is required.

        For large files it's recommended to use multipart upload. You can do this by providing a filename and NOT a
        package. When you do such a request, in the response you will get uploading info.

        If the upload info is of type `askanna` you can use the `upload_info.url` to upload file parts. By adding
        `part` to the url you can upload a file part. When all parts are uploaded you can do a request to complete
        the file by adding `complete` to the url. See the `storage` section in the API documentation for more info.

        If the upload info is of type `minio` you can use the `upload_info.url` as a presigned url to upload the file.

        By providing optional values for `size` and `etag` in the request body, the file will be validated against
        these values. If the values are not correct, the upload will fail.
        """
        if "package" not in request.FILES.keys() and "filename" not in request.data.keys():
            return Response({"detail": ("Package or filename is required")}, status=status.HTTP_400_BAD_REQUEST)

        self.serializer_class = (
            PackageCreateWithFileSerializer if request.FILES.get("package") else PackageCreateWithoutFileSerializer
        )

        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve information about a package. This includes the package meta data, download info and a list of files
        that are part of the package.

        If the download info is of type `askanna` the `download_info.url` can be used to download the package or to
        get a specific file from the package you add the query parameter `file_path` to the url. See the `storage`
        section in the API documentation for more info.
        """
        self.serializer_class = PackageSerializerWithFileList
        return super().retrieve(request, *args, **kwargs)

    def perform_destroy(self, instance):
        instance.to_deleted()
