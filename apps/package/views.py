from pathlib import Path

import django_filters
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Case, Q, When
from django.http import Http404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotAuthenticated
from rest_framework.response import Response

from account.models.membership import MSP_WORKSPACE, Membership
from core.filters import filter_multiple
from core.mixins import ObjectRoleMixin, SerializerByActionMixin
from core.permissions.role import RoleBasedPermission
from core.views import BaseChunkedPartViewSet, BaseUploadFinishViewSet
from package.models import ChunkedPackagePart, Package
from package.serializers.chunked_package import ChunkedPackagePartSerializer
from package.serializers.package import (
    PackageCreateSerializer,
    PackageSerializer,
    PackageSerializerWithFileList,
)
from package.signals import package_upload_finish
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
        field_name="member__suuid",
        method=filter_multiple,
        help_text="Filter packages on a created by suuid or multiple created by suuids via a comma seperated list.",
    )
    created_by_name = django_filters.CharFilter(
        field_name="member_name",
        lookup_expr="icontains",
        help_text="Filter packages on a created by name.",
    )


@extend_schema_view(
    list=extend_schema(description="List packages you have access to"),
    create=extend_schema(description="Do a request to upload a new package"),
    retrieve=extend_schema(description="Get info from a specific package"),
)
class PackageViewSet(
    ObjectRoleMixin,
    SerializerByActionMixin,
    BaseUploadFinishViewSet,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List all packages and allow to finish upload action
    """

    queryset = (
        Package.objects.active()
        .select_related("project", "project__workspace", "created_by", "member", "member__user")
        .annotate(
            member_name=Case(
                When(member__use_global_profile=True, then="created_by__name"),
                When(member__use_global_profile=False, then="member__name"),
            ),
        )
    )
    lookup_field = "suuid"
    search_fields = ["suuid", "name", "original_filename"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "filename",
        "project.name",
        "project.suuid",
        "workspace.name",
        "workspace.suuid",
        "created_by.name",
    ]
    ordering_fields_aliases = {
        "filename": "original_filename",
        "workspace.name": "project__workspace__name",
        "workspace.suuid": "project__workspace__suuid",
        "created_by.name": "member_name",
    }
    filterset_class = PackageFilterSet

    serializer_class = PackageSerializer
    serializer_class_by_action = {
        "retrieve": PackageSerializerWithFileList,
        "create": PackageCreateSerializer,
    }

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.code.list"],
        "retrieve": ["project.code.list"],
        "create": ["project.code.create"],
        "finish_upload": ["project.code.create"],
        "download": ["project.code.list"],
    }

    upload_finished_signal = package_upload_finish
    upload_finished_message = "package upload finished"

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        user = self.request.user
        if user.is_anonymous:
            queryset = (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        else:
            member_of_workspaces = user.memberships.filter(
                object_type=MSP_WORKSPACE, deleted_at__isnull=True
            ).values_list("object_uuid", flat=True)

            queryset = (
                super()
                .get_queryset()
                .filter(
                    Q(project__workspace__pk__in=member_of_workspaces)
                    | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
                )
            )

        if self.action == "finish_upload":
            return queryset.filter(finished_at__isnull=True)
        return queryset.filter(finished_at__isnull=False)

    def get_object_project(self):
        return self.current_object.project

    def get_parrent_roles(self, request, *args, **kwargs):
        """
        The role for creating a package is based on the project and workspace. To create a package you need to be
        authenticated.
        For creating a package there is an indirect parent lookup because the project_suuid is part of the payload.
        To get the parrent roles, we read the project SUUID from the payload and determine the user's role.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            project_suuid = request.data.get("project_suuid")
            try:
                project = Project.objects.active().get(suuid=project_suuid)
            except Project.DoesNotExist as exc:
                raise Http404 from exc

            return Membership.get_roles_for_project(request.user, project)

        return []

    def get_upload_location(self, obj) -> Path:
        directory = settings.UPLOAD_ROOT / "project" / obj.project.suuid
        Path.mkdir(directory, parents=True, exist_ok=True)
        return directory

    def get_target_location(self, request, obj, **kwargs) -> Path:
        return settings.PACKAGES_ROOT / obj.storage_location

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        # we specify the "member" also in the update_fields
        # because this will be updated later in a listener
        instance_obj.finished_at = timezone.now()
        instance_obj.save(
            update_fields=[
                "member",
                "finished_at",
                "modified_at",
            ]
        )

    @action(detail=True, methods=["get"])
    def download(self, request, **kwargs):
        """
        Get info to download a package

        The request returns a response with the URI on the CDN where to find the package file.
        """
        package = self.get_object()

        return Response(
            {
                "action": "redirect",
                "target": "{BASE_URL}/files/packages/{LOCATION}/{FILENAME}".format(
                    BASE_URL=settings.ASKANNA_CDN_URL,
                    LOCATION=package.storage_location,
                    FILENAME=package.filename,
                ),
            }
        )


class ChunkedPackagePartViewSet(ObjectRoleMixin, BaseChunkedPartViewSet):
    """Request an uuid to upload a package chunk"""

    queryset = ChunkedPackagePart.objects.all().select_related(
        "package__project",
        "package__project__workspace",
    )
    serializer_class = ChunkedPackagePartSerializer
    permission_classes = [RoleBasedPermission]

    rbac_permissions_by_action = {
        "list": ["project.code.list"],
        "retrieve": ["project.code.list"],
        "create": ["project.code.create"],
        "chunk": ["project.code.create"],
    }

    def get_upload_location(self, chunkpart) -> Path:
        directory = settings.UPLOAD_ROOT / "project" / chunkpart.package.project.suuid
        Path.mkdir(directory, parents=True, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.package.project

    def get_parrent_roles(self, request, *args, **kwargs):
        """
        The role for creating a package chunk is based on the package.
        For creating a package chunk there is an indirect parent lookup because the package is linked to the project.
        To get the parrent roles, we get the project from the package and determine the user's role.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            parents = self.get_parents_query_dict()
            try:
                package = Package.objects.get(suuid=parents.get("package__suuid"))
                project = package.project
            except ObjectDoesNotExist as exc:
                raise Http404 from exc

            return Membership.get_roles_for_project(request.user, project)

        return []

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        suuid = parents.get("package__suuid")
        request.data.update(
            **{
                "package": str(
                    Package.objects.get(
                        suuid=suuid,
                    ).pk
                )
            }
        )
