from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin

from resumable.files import ResumableFile

from core.mixins import HybridUUIDMixin
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer

from rest_framework.schemas.openapi import AutoSchema

class MySchema(AutoSchema):
    def get_tags(self, path, method):
        return ['workspace']

class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    schema = MySchema()
