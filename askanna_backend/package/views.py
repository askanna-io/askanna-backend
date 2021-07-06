# -*- coding: utf-8 -*-
import os
from django.conf import settings

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import (
    BaseChunkedPartViewSet,
    BaseUploadFinishMixin,
    SerializerByActionMixin,
)
from job.permissions import (
    IsMemberOfProjectAttributePermission,
    IsMemberOfPackageAttributePermission,
)
from package.models import Package, ChunkedPackagePart
from package.serializers import (
    PackageSerializer,
    ChunkedPackagePartSerializer,
    PackageSerializerDetail,
    PackageCreateSerializer,
)
from package.signals import package_upload_finish
from users.models import MSP_WORKSPACE


class PackageViewSet(
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

    queryset = Package.objects.all()
    lookup_field = "short_uuid"
    serializer_class = PackageSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

    upload_target_location = settings.PACKAGES_ROOT
    upload_finished_signal = package_upload_finish
    upload_finished_message = "package upload finished"

    serializer_classes_by_action = {
        "post": PackageCreateSerializer,
    }

    def get_queryset(self):
        """
        Filter only the packages where the user has access to.
        Meaning all packages within projects/workspaces the user has joined
        Only for the list action, the limitation for other cases is covered with permissions
        """
        if self.action == "list":
            user = self.request.user
            member_of_workspaces = user.memberships.filter(
                object_type=MSP_WORKSPACE
            ).values_list("object_uuid")

            return (
                super()
                .get_queryset()
                .filter(project__workspace__pk__in=member_of_workspaces)
            )
        return super().get_queryset()

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return obj.filename

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["created_by"]
        instance_obj.created_by = request.user
        instance_obj.save(update_fields=update_fields)


class ChunkedPackagePartViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of packages
    """

    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer
    permission_classes = [IsMemberOfPackageAttributePermission]

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


class ProjectPackageViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):

    queryset = Package.objects.exclude(original_filename="")
    lookup_field = "short_uuid"
    serializer_class = PackageSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

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
