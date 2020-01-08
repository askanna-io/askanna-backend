from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from uploadfile.models import DummyFile
from uploadfile.serializers import DummyFileSerializer


class DummyFileViewSet(viewsets.ModelViewSet):
    queryset = DummyFile.objects.all()
    # parser_classes = [FileUploadParser, ]
    serializer_class = DummyFileSerializer
