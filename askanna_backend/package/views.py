from django.shortcuts import render
from django.core.files.storage import FileSystemStorage

from package.models import Package, ChunkedPackagePart
from package.serializers import PackageSerializer, ChunkedPackagePartSerializer
from rest_framework import viewsets
from rest_framework.decorators import action

from rest_framework.decorators import action
from rest_framework.response import Response

from resumable.files import ResumableFile

class PackageViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Package.objects.all()
    serializer_class = PackageSerializer


class ChunkedPackagePartViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer

    @action(detail=True, methods=['post'])
    def chunk_receiver(self, request, **kwargs):
        """
        Receives one chunk in the POST request 

        """
        print(kwargs)
        chunkpart = self.get_object()
        chunk = request.FILES.get('file')
        print(request.POST)

        storage_location = FileSystemStorage(location='/tmp')

        r = ResumableFile(storage_location, request.POST)
        if r.chunk_exists:
            return Response('chunk already exists')
        r.process_chunk(chunk)

        chunkpart.filename = '%s%s%s' % (
                r.filename,
                r.chunk_suffix,
                r.kwargs.get('resumableChunkNumber').zfill(4))
        chunkpart.save()

        return Response({
            'uuid': str(chunkpart.uuid)
        })


# Userflow for uploading chunk
# 1. create package entry
# 2. create chunk entry (via api)
# 3. update chunk entry
# 4. repeat step 2-3 if more chunks