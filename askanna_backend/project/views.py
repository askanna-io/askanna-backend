# -*- coding: utf-8 -*-
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import PermissionByActionMixin, SerializerByActionMixin
from users.models import MSP_WORKSPACE
from .models import Project
from .permissions import (
    IsMemberOfProjectWorkspacePermission,
    IsAdminOfProjectWorkspacePermission,
)
from .serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
)


class ProjectView(
    PermissionByActionMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.projects.active()
    serializer_class = ProjectSerializer
    lookup_field = "short_uuid"
    permission_classes = [IsMemberOfProjectWorkspacePermission]

    serializer_classes_by_action = {
        "post": ProjectCreateSerializer,
        "put": ProjectUpdateSerializer,
        "patch": ProjectUpdateSerializer,
    }

    permission_classes_by_action = {
        "destroy": [IsAdminOfProjectWorkspacePermission],
    }

    def get_queryset(self):
        """
        Filter only the projects where the user has access to.
        Meaning all projects within workspaces the user has joined
        Only for the list action, the limitation for other cases is covered with permissions
        """
        if self.action == "list":
            user = self.request.user
            member_of_workspaces = user.memberships.filter(
                object_type=MSP_WORKSPACE
            ).values_list("object_uuid")

            return super().get_queryset().filter(workspace__pk__in=member_of_workspaces)
        return super().get_queryset()

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()


class ProjectReadOnlyView(
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.projects.active()
    serializer_class = ProjectSerializer
    lookup_field = "short_uuid"
    permission_classes = [IsMemberOfProjectWorkspacePermission]

    def get_queryset(self):
        """
        Filter only the projects where the user has access to.
        Meaning all projects within workspaces the user has joined
        Only for the list action, the limitation for other cases is covered with permissions
        """
        if self.action == "list":
            user = self.request.user
            member_of_workspaces = user.memberships.filter(
                object_type=MSP_WORKSPACE
            ).values_list("object_uuid")

            return super().get_queryset().filter(workspace__pk__in=member_of_workspaces)
        return super().get_queryset()
