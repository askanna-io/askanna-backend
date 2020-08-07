from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin

from project_template.models import ProjectTemplate
from project_template.serializers import ProjectTemplateSerializer


class ProjectTemplateListView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = ProjectTemplate.objects.all()
    serializer_class = ProjectTemplateSerializer
    lookup_field = "short_uuid"
    permission_classes = [IsAuthenticated]
