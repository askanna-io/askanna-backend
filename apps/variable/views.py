import django_filters
from django.db.models import Q
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.exceptions import NotAuthenticated

from account.models.membership import MSP_WORKSPACE, Membership
from core.filters import filter_multiple
from core.mixins import (
    ObjectRoleMixin,
    PartialUpdateModelMixin,
    SerializerByActionMixin,
)
from core.permissions.role import RoleBasedPermission
from project.models import Project
from variable.models import Variable
from variable.serializers import VariableCreateSerializer, VariableSerializer


class VariableFilterSet(django_filters.FilterSet):
    is_masked = django_filters.BooleanFilter(help_text="Filter on variables where value is masked.")
    project_suuid = django_filters.CharFilter(
        field_name="project__suuid",
        method=filter_multiple,
        help_text="Filter variables on a project suuid or multiple project suuids via a comma seperated list.",
    )
    workspace_suuid = django_filters.CharFilter(
        field_name="project__workspace__suuid",
        method=filter_multiple,
        help_text="Filter variables on a workspace suuid or multiple workspace suuids via a comma seperated list.",
    )


@extend_schema_view(
    list=extend_schema(description="List variables you have access to"),
    retrieve=extend_schema(description="Get info from a specific variable"),
    create=extend_schema(description="Create a new variable for a project"),
    partial_update=extend_schema(description="Update a variable"),
    destroy=extend_schema(description="Remove a variable"),
)
class VariableView(
    ObjectRoleMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Variable.objects.active().select_related("project", "project__workspace")
    lookup_field = "suuid"
    search_fields = ["suuid", "name"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "is_masked",
        "project.suuid",
        "project.name",
        "workspace.suuid",
        "workspace.name",
    ]
    ordering_fields_aliases = {
        "workspace.suuid": "project__workspace__suuid",
        "workspace.name": "project__workspace__name",
    }
    filterset_class = VariableFilterSet

    serializer_class = VariableSerializer
    serializer_class_by_action = {
        "create": VariableCreateSerializer,
    }

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "list": ["variable.list"],
        "retrieve": ["variable.list"],
        "create": ["variable.create"],
        "destroy": ["variable.remove"],
        "partial_update": ["variable.edit"],
    }

    def get_object_project(self):
        return self.current_object.project

    def get_parrent_roles(self, request, *args, **kwargs):
        """
        The role for creating a variable is based on the project and workspace. To create a variable you need to be
        authenticated.
        For creating a variable there is an indirect parent lookup because the project_suuid is part of the payload.
        To get the parrent roles, we read the project SUUID from the payload and determine the user's role.
        """
        if self.action == "create":
            if request.user.is_anonymous:
                raise NotAuthenticated

            project_suuid = request.data.get("project_suuid")
            try:
                project = Project.objects.active().get(suuid=project_suuid)
            except Project.DoesNotExist as exc:
                raise Http404 from exc

            return Membership.get_roles_for_project(request.user, project)

        return []

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE, deleted_at__isnull=True).values_list(
            "object_uuid", flat=True
        )

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__pk__in=member_of_workspaces)
                | (Q(project__workspace__visibility="PUBLIC") & Q(project__visibility="PUBLIC"))
            )
        )
