# -*- coding: utf-8 -*-
import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from django.utils import timezone
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
    SerializerByActionMixin,
    ObjectRoleMixin,
    workspace_to_project_role,
)
from core.permissions import (
    ProjectMember,
    ProjectNoMember,
    RoleBasedPermission,
)
from package.models import Package, ChunkedPackagePart
from package.serializers import (
    PackageSerializer,
    ChunkedPackagePartSerializer,
    PackageSerializerDetail,
    PackageCreateSerializer,
)
from package.signals import package_upload_finish
from project.models import Project
from users.models import MSP_WORKSPACE, Membership


class PackageObjectRoleMixin:
    def get_object_project(self):
        return self.current_object.project

    def get_object_workspace(self):
        return self.current_object.project.workspace

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_create_role(self, request, *args, **kwargs):
        project_suuid = request.data.get("project")
        try:
            project = Project.objects.get(short_uuid=project_suuid)
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

    def get_queryset(self):

        """
        Filter only the packages where the user has access to.
        Meaning all packages within projects/workspaces the user has joined
        Only for the list action, the limitation for other cases is covered with permissions
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
                .order_by("name")
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid")

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__pk__in=member_of_workspaces)
                | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        )


class PackageViewSet(
    PackageObjectRoleMixin,
    ObjectRoleMixin,
    SerializerByActionMixin,
    BaseUploadFinishMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """
    List all packages and allow to finish upload action
    """

    queryset = Package.objects.exclude(original_filename="").select_related("project", "project__workspace")
    lookup_field = "short_uuid"
    serializer_class = PackageSerializer
    permission_classes = [RoleBasedPermission]

    upload_target_location = settings.PACKAGES_ROOT
    upload_finished_signal = package_upload_finish
    upload_finished_message = "package upload finished"

    serializer_classes_by_action = {
        "post": PackageCreateSerializer,
    }

    RBAC_BY_ACTION = {
        "list": ["project.code.list"],
        "retrieve": ["project.code.list"],
        "create": ["project.code.create"],
        "finish_upload": ["project.code.create"],
    }

    def get_upload_dir(self, obj):
        # directory structure is containing the project-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "project", obj.project.short_uuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return obj.filename

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        # we specify the "member" also in the update_fields
        # because this will be updated later in a listener
        instance_obj.finished = timezone.now()
        update_fields = ["member", "finished"]
        instance_obj.save(update_fields=update_fields)


class ChunkedPackagePartViewSet(ObjectRoleMixin, BaseChunkedPartViewSet):
    """
    Allow chunked uploading of packages
    """

    queryset = ChunkedPackagePart.objects.all().select_related(
        "package__project",
        "package__project__workspace",
    )
    serializer_class = ChunkedPackagePartSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.code.list"],
        "retrieve": ["project.code.list"],
        "create": ["project.code.create"],
        "chunk": ["project.code.create"],
    }

    def get_upload_dir(self, chunkpart):
        # directory structure is containing the project-suuid
        directory = os.path.join(settings.UPLOAD_ROOT, "project", chunkpart.package.project.short_uuid)
        if not os.path.isdir(directory):
            os.makedirs(directory, exist_ok=True)
        return directory

    def get_object_project(self):
        return self.current_object.package.project

    def get_object_workspace(self):
        return self.current_object.package.project.workspace

    def get_create_role(self, request, *args, **kwargs):
        parents = self.get_parents_query_dict()
        try:
            package = Package.objects.get(short_uuid=parents.get("package__short_uuid"))
            project = package.project
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

    def initial(self, request, *args, **kwargs):
        """
        Set and lookup external relation by default
        """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        short_uuid = parents.get("package__short_uuid")
        request.data.update(
            **{
                "package": str(
                    Package.objects.get(
                        short_uuid=short_uuid,
                    ).pk
                )
            }
        )


class ProjectPackageViewSet(
    NestedViewSetMixin, PackageObjectRoleMixin, ObjectRoleMixin, viewsets.ReadOnlyModelViewSet
):

    queryset = (
        Package.objects.exclude(original_filename="")
        .filter(finished__isnull=False)
        .select_related("project", "project__workspace")
    )
    lookup_field = "short_uuid"
    serializer_class = PackageSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.code.list"],
        "retrieve": ["project.code.list"],
        "download": ["project.code.list"],
    }

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        parents = self.get_parents_query_dict()
        project = Project.objects.get(short_uuid=parents.get("project__short_uuid"))
        request.user_roles += Membership.get_roles_for_project(request.user, project)

        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_serializer_class(self):
        if self.action == "retrieve":
            return PackageSerializerDetail
        return self.serializer_class

    @action(detail=True, methods=["get"])
    def download(self, request, **kwargs):
        """
        Return a response with the URI on the CDN where to find the full package.
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
