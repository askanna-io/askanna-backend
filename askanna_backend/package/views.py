from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework import status
from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from core.mixins import HybridUUIDMixin
from core.views import BaseChunkedPartViewSet, BaseUploadFinishMixin
from package.listeners import *
from package.models import Package, ChunkedPackagePart
from package.serializers import (
    PackageSerializer,
    ChunkedPackagePartSerializer,
    PackageSerializerDetail,
    PackageCreateSerializer,
)
from package.signals import package_upload_finish


class PackageViewSet(
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
    permission_classes = [IsAuthenticated]

    upload_target_location = settings.PACKAGES_ROOT
    upload_finished_signal = package_upload_finish
    upload_finished_message = "package upload finished"

    def get_serializer_class(self):
        if self.request.method.upper() in ["POST"]:
            return PackageCreateSerializer
        return self.serializer_class

    def store_as_filename(self, resumable_filename: str, obj) -> str:
        return obj._filename

    def get_upload_target_location(self, request, obj, **kwargs) -> str:
        return os.path.join(self.upload_target_location, obj.new_storage_location)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["created_by", "original_filename", "size"]
        instance_obj.original_filename = resume_obj.filename
        instance_obj.created_by = request.user
        instance_obj.size = resume_obj.size
        instance_obj.save(update_fields=update_fields)


class ChunkedPackagePartViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of packages
    """

    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer
    permission_classes = [IsAuthenticated]


class ProjectPackageViewSet(
    HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet
):

    queryset = Package.objects.all()
    lookup_field = "short_uuid"
    serializer_class = PackageSerializer
    permission_classes = [IsAuthenticated]

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
                    LOCATION=package.new_storage_location,
                    FILENAME=package._filename,
                ),
            }
        )
