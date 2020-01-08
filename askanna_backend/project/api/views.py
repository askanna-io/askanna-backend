from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import (CreateAPIView, UpdateAPIView,
                                     RetrieveUpdateDestroyAPIView)
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from project.models import Project
from project.api.serializers import ProjectSerializer


class ProjectListView(RetrieveAPIView):
    """
    Read only view for a specific Dataset
    """

    model = Project
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    permission_classes = (
        IsAuthenticated
    )
    authentication_classes = (
        SessionAuthentication
    )
    permissions = ('project.view_project',)

