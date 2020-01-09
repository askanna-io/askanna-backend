from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from job.models import Job
from job.api.serializers import JobSerializer


class ProjectListView(viewsets.ModelViewSet):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
