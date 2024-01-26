import django_filters
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.exceptions import NotAuthenticated

from account.models.membership import Membership
from core.filters import case_insensitive, filter_multiple
from core.mixins import (
    ObjectRoleMixin,
    PartialUpdateModelMixin,
    SerializerByActionMixin,
)
from core.permissions import RoleBasedPermission
from core.permissions.role_utils import get_user_workspace_role
from core.viewsets import AskAnnaGenericViewSet
from project.models import Project
from project.serializers import ProjectCreateSerializer, ProjectSerializer
from workspace.models import Workspace


class ProjectFilterSet(django_filters.FilterSet):
    is_member = django_filters.BooleanFilter(help_text="Filter on projects where the account is a member.")
    visibility = django_filters.ChoiceFilter(
        choices=(("public", "PUBLIC"), ("private", "PRIVATE")),
        method=case_insensitive,
        help_text="Filter projects on visibility.",
    )
    workspace_suuid = django_filters.CharFilter(
        field_name="workspace__suuid",
        method=filter_multiple,
        help_text="Filter projects on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )


@extend_schema_view(
    list=extend_schema(description="List the projects you have access to"),
    retrieve=extend_schema(description="Get info from a specific project"),
    create=extend_schema(description="Create a new project"),
    partial_update=extend_schema(description="Update a project"),
    destroy=extend_schema(description="Remove a project"),
)
class ProjectView(
    ObjectRoleMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    queryset = Project.objects.active(add_select_related=True)
    search_fields = ["suuid", "name"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "visibility",
        "is_member",
        "workspace.suuid",
        "workspace.name",
    ]
    filterset_class = ProjectFilterSet

    serializer_class = ProjectSerializer
    serializer_class_by_action = {
        "create": ProjectCreateSerializer,
    }

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["project.list"],
        "retrieve": ["project.info.view"],
        "create": ["project.create"],
        "destroy": ["project.remove"],
        "partial_update": ["project.info.edit"],
    }

    def get_queryset(self):
        """
        Return only projects where the user is member of or has access to because it's public.
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(workspace__visibility="PUBLIC") & Q(visibility="PUBLIC"))
                .annotate(is_member=Value(False, BooleanField()))
            )

        memberships = Membership.objects.active_members().filter(
            Q(user=user, object_uuid=OuterRef("pk")) | Q(user=user, object_uuid=OuterRef("workspace__pk"))
        )

        return (
            super()
            .get_queryset()
            .filter(
                Q(workspace__pk__in=self.member_of_workspaces)
                | (Q(workspace__visibility="PUBLIC") & Q(visibility="PUBLIC"))
            )
            .annotate(is_member=Exists(memberships))
        )

    def get_object_project(self):
        return self.current_object

    def get_parrent_roles(self, request, *args, **kwargs):
        """
        The role for creating a project is based on the workspace. To create a project you need to be authenticated.
        For creating a project there is an indirect parent lookup because the workspace_suuid is part of the payload.
        To get the parrent roles, we read the workspace SUUID from the payload and determine the user's role.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            workspace_suuid = request.data.get("workspace_suuid")
            try:
                workspace = Workspace.objects.active().get(suuid=workspace_suuid)
            except Workspace.DoesNotExist as exc:
                raise Http404 from exc

            return [get_user_workspace_role(request.user, workspace)]

        return []

    def perform_destroy(self, instance):
        instance.to_deleted()
