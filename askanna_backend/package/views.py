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
from package.serializers import PackageSerializer, ChunkedPackagePartSerializer, PackageSerializerDetail, PackageCreateSerializer
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

    def create(self, request, *args, **kwargs):
        """
        Create a model instance. Overwrite for create /POST
        """
        serializer = PackageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def post_finish_upload_update_instance(self, request, instance_obj, resume_obj):
        update_fields = ["created_by", "storage_location", "size"]
        instance_obj.storage_location = resume_obj.filename
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

    # overwrite the default view and serializer for detail page
    # we want to use an other serializer for this.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs["context"] = self.get_serializer_context()
        serializer = PackageSerializerDetail(instance, **serializer_kwargs)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download(self, request, **kwargs):
        package = self.get_object()

        return Response(
            {
                "action": "redirect",
                "target": "{scheme}://{FQDN}/files/packages/{LOCATION}".format(
                    scheme=request.scheme,
                    FQDN=settings.ASKANNA_CDN_FQDN,
                    LOCATION=package.storage_location,
                ),
            }
        )
