import django_filters
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets

from account.models.membership import MSP_WORKSPACE, Membership
from core.filters import case_insensitive
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.role import RoleBasedPermission
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer


class WorkspaceFilterSet(django_filters.FilterSet):
    is_member = django_filters.BooleanFilter(help_text="Filter on workspaces where the account is a member.")
    visibility = django_filters.ChoiceFilter(
        choices=(("public", "PUBLIC"), ("private", "PRIVATE")),
        help_text="Filter workspaces on visibility.",
        method=case_insensitive,
    )


@extend_schema_view(
    list=extend_schema(description="List the workspaces you have access to"),
    retrieve=extend_schema(description="Get info from a specific workspace"),
    create=extend_schema(description="Create a new workspace"),
    partial_update=extend_schema(description="Update a workspace"),
    destroy=extend_schema(description="Remove a workspace"),
)
class WorkspaceViewSet(
    ObjectRoleMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Workspace.objects.active().select_related("created_by_user", "created_by_member__user")
    serializer_class = WorkspaceSerializer
    lookup_field = "suuid"
    search_fields = ["suuid", "name"]
    ordering_fields = ["created_at", "modified_at", "name", "visibility", "is_member"]
    filterset_class = WorkspaceFilterSet

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["workspace.list"],
        "retrieve": ["workspace.info.view"],
        "create": ["workspace.create"],
        "partial_update": ["workspace.info.edit"],
        "destroy": ["workspace.remove"],
    }

    def get_queryset(self):
        """
        Return only workspaces where the user is member of or has access to
        """
        user = self.request.user
        if user.is_anonymous:
            return super().get_queryset().filter(visibility="PUBLIC").annotate(is_member=Value(False, BooleanField()))

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE, deleted_at__isnull=True).values_list(
            "object_uuid"
        )

        memberships = Membership.objects.filter(user=user, deleted_at__isnull=True, object_uuid=OuterRef("pk"))

        return (
            super()
            .get_queryset()
            .filter(Q(pk__in=member_of_workspaces) | Q(visibility="PUBLIC"))
            .annotate(is_member=Exists(memberships))
        )

    def get_object_workspace(self):
        return self.current_object

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()
