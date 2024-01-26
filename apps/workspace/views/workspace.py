import django_filters
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins

from account.models.membership import Membership
from core.filters import case_insensitive
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions import RoleBasedPermission
from core.viewsets import AskAnnaGenericViewSet
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
    AskAnnaGenericViewSet,
):
    queryset = Workspace.objects.active().select_related("created_by_user", "created_by_member__user")
    serializer_class = WorkspaceSerializer

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

        memberships = Membership.objects.active_members().filter(user=user, object_uuid=OuterRef("pk"))

        return (
            super()
            .get_queryset()
            .filter(Q(pk__in=self.member_of_workspaces) | Q(visibility="PUBLIC"))
            .annotate(is_member=Exists(memberships))
        )

    def get_object_workspace(self):
        return self.current_object

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()
