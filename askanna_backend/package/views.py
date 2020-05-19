from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from core.mixins import HybridUUIDMixin
from core.views import BaseChunkedPartViewSet
from package.listeners import *
from package.models import Package, ChunkedPackagePart
from package.serializers import PackageSerializer, ChunkedPackagePartSerializer, PackageSerializerDetail
from package.signals import package_upload_finish


class PackageViewSet(mixins.CreateModelMixin,
                        mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        viewsets.GenericViewSet):
    """
    List all apckages and allow to finish upload action
    """

    queryset = Package.objects.all()
    serializer_class = PackageSerializer

    @action(detail=True, methods=["post"])
    def finish_upload(self, request, **kwargs):
        package = self.get_object()

        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)
        target_location = FileSystemStorage(location=settings.PACKAGES_ROOT)
        r = ResumableFile(storage_location, request.POST)
        if r.is_complete:
            target_location.save(r.filename, r)
            package.storage_location=r.filename
            package.created_by = request.user
            package.save(update_fields=['storage_location', 'created_by'])
            r.delete_chunks()

            package_upload_finish.send(
                sender=self.__class__, postheaders=dict(request.POST.lists()), package=package
            )

        # FIXME: make return message relevant
        response = Response({"message": "package upload finished"}, status=200)
        response["Cache-Control"] = "no-cache"
        return response


class ChunkedPackagePartViewSet(BaseChunkedPartViewSet):
    """
    Allow chunked uploading of packages
    """
    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer


class ProjectPackageViewSet(HybridUUIDMixin, NestedViewSetMixin, 
                            viewsets.ReadOnlyModelViewSet):

    queryset = Package.objects.all()
    serializer_class = PackageSerializer

    # overwrite the default view and serializer for detail page
    # we want to use an other serializer for this.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs['context'] = self.get_serializer_context()
        serializer = PackageSerializerDetail(instance, **serializer_kwargs)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def download(self, request, **kwargs):
        package = self.get_object()

        return Response({
            "action": "redirect",
            "target": "https://{FQDN}/files/packages/{LOCATION}".format(
                FQDN=settings.ASKANNA_CDN_FQDN,
                LOCATION=package.storage_location
            )
        })
