from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from package.listeners import *
from package.models import Package, ChunkedPackagePart
from package.serializers import PackageSerializer, ChunkedPackagePartSerializer, PackageSerializerDetail
from package.signals import package_upload_finish


class PackageViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
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
            # FIXME: do the following in a worker to offload load:
            # store file to settings.PACKAGES_ROOT
            # r.delete_chunks()
            package_upload_finish.send(
                sender=self.__class__, postheaders=dict(request.POST.lists())
            )
            target_location.save(r.filename, r)
            package.storage_location=r.filename
            package.save()
            r.delete_chunks()

        # FIXME: make return message relevant
        response = Response({"message": "package upload finished"}, status=200)
        response["Cache-Control"] = "no-cache"
        return response


class ChunkedPackagePartViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """

    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer

    def check_existence(self, request, **kwargs):
        """
        We check the existence of a potential chunk to be uploaded.
        This prevents a new POST action from the client and we don't
        have to process this (saves time)
        """
        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)

        r = ResumableFile(storage_location, request.GET)
        response = None
        if r.chunk_exists:
            response = Response({"message": "chunk already exists"}, status=200)
        response = Response({"message": "chunk upload needed"}, status=404)
        response["Cache-Control"] = "no-cache"
        return response

    @action(detail=True, methods=["post", "get"])
    def chunk_receiver(self, request, **kwargs):
        """
        Receives one chunk in the POST request 

        """
        chunkpart = self.get_object()

        if request.method == "GET":
            return self.check_existence(request, **kwargs)
        chunk = request.FILES.get("file")
        storage_location = FileSystemStorage(location=settings.UPLOAD_ROOT)

        r = ResumableFile(storage_location, request.POST)
        if r.chunk_exists:
            return Response({"message": "chunk already exists"}, status=200)
        r.process_chunk(chunk)

        chunkpart.filename = "%s%s%s" % (
            r.filename,
            r.chunk_suffix,
            r.kwargs.get("resumableChunkNumber").zfill(4),
        )
        chunkpart.save()

        return Response(
            {"uuid": str(chunkpart.uuid), "message": "chunk stored"}, status=200
        )


class ProjectPackageViewSet(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):

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

    @action(detail=True, methods=["post"])
    def download(self, request, **kwargs):
        package = self.get_object()

        return Response({
            "action": "redirect",
            "target": "https://{FQDN}/files/{LOCATION}".format(
                FQDN=settings.ASKANNA_CDN_FQDN,
                LOCATION=package.storage_location
            )
        })
