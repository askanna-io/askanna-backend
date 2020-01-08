from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from project.models import Project
from project.api.serializers import ProjectSerializer


class ProjectListView(viewsets.ReadOnlyModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
