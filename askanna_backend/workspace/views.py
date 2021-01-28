import django_filters
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer


class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    lookup_field = "short_uuid"
    permission_classes = [IsAuthenticated]

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


class RoleFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name="role")

    class Meta:
        model = Membership
        fields = ["role"]
