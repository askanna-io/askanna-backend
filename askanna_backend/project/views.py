from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated

from rest_framework_extensions.mixins import NestedViewSetMixin

from project.models import Project
from project.serializers import ProjectSerializer, ProjectCreateSerializer, ProjectUpdateSerializer
from users.permissions import IsMemberOrAdminUser


class ProjectView(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    lookup_field = "short_uuid"
    permission_classes = [IsMemberOrAdminUser]

    def get_serializer_class(self):
        """
        Return different serializer class for POST
        """
        if self.request.method.upper() in ["POST"]:
            return ProjectCreateSerializer
        elif self.request.method.upper() in ["PUT", "PATCH"]:
            return ProjectUpdateSerializer
        return self.serializer_class
