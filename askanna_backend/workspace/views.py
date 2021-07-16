# -*- coding: utf-8 -*-
import django_filters
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from core.views import (
    PermissionByActionMixin,
)
from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace
from workspace.permissions import (
    IsWorkspaceAdminBasePermission,
    IsWorkspaceMemberBasePermission,
)
from workspace.serializers import WorkspaceSerializer


class WorkspaceViewSet(
    PermissionByActionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Workspace.objects.filter(deleted__isnull=True)
    serializer_class = WorkspaceSerializer
    lookup_field = "short_uuid"
    permission_classes = [
        IsAuthenticated,
    ]

    permission_classes_by_action = {
        "list": [IsWorkspaceMemberBasePermission],
        "create": [
            IsAuthenticated,
        ],
        "update": [
            IsWorkspaceMemberBasePermission | IsWorkspaceAdminBasePermission,
        ],
        "destroy": [IsWorkspaceAdminBasePermission],
        "partial_update": [
            IsWorkspaceMemberBasePermission | IsWorkspaceAdminBasePermission,
        ],
    }

    def get_queryset(self):
        """
        Return only where the user is member of or has access to
        FIXME: get rid of the query here, store in redis in future
        """
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE, deleted__isnull=True
        ).values_list("object_uuid")

        return self.queryset.filter(pk__in=member_of_workspaces)

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()


class RoleFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name="role")

    class Meta:
        model = Membership
        fields = ["role"]
