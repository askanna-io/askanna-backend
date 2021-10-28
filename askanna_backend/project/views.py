# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q, Exists, OuterRef, Value, BooleanField
from django.http import Http404
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.permissions import (
    ProjectNoMember,
    RoleBasedPermission,
    PublicViewer,
)
from core.views import SerializerByActionMixin, ObjectRoleMixin
from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace
from .models import Project
from .serializers import (
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
)


class FilterByMembershipFilterSet(django_filters.FilterSet):
    membership = django_filters.CharFilter(field_name="membership", method="filter_membership")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created", "created"),
            ("is_member", "membership"),
            ("name", "name"),
        )
    )

    def filter_membership(self, queryset, name, value):
        # construct the full lookup expression.
        bool_value = value.lower() in ["1", "yes", "true"]
        lookup = "is_member"
        return queryset.filter(**{lookup: bool_value})

    class Meta:
        model = Project
        fields = ["membership"]


class ProjectRoleMixin:

    # Override default, remove OrderingFilter because we use the DjangoFilterBackend version
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterByMembershipFilterSet

    def get_queryset(self):
        """
        Filter only the projects where the user has access to.
        Meaning all projects within workspaces the user has joined
        Only for the list action, the limitation for other cases is covered with permissions
        """
        user = self.request.user

        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(workspace__visibility="PUBLIC") & Q(visibility="PUBLIC"))
                .annotate(is_member=Value(False, BooleanField()))
                .order_by("name")
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid")

        memberships = Membership.objects.filter(
            Q(user=user, deleted__isnull=True, object_uuid=OuterRef("pk"))
            | Q(user=user, deleted__isnull=True, object_uuid=OuterRef("workspace__pk"))
        )

        return (
            super()
            .get_queryset()
            .filter(
                Q(workspace__pk__in=member_of_workspaces)
                | (Q(workspace__visibility="PUBLIC") & Q(visibility="PUBLIC"))
            )
            .annotate(is_member=Exists(memberships))
            .order_by("name")
        )


class ProjectView(
    ProjectRoleMixin,
    ObjectRoleMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.projects.active().select_related("workspace")
    serializer_class = ProjectSerializer
    lookup_field = "short_uuid"
    permission_classes = [RoleBasedPermission]

    serializer_classes_by_action = {
        "post": ProjectCreateSerializer,
        "put": ProjectUpdateSerializer,
        "patch": ProjectUpdateSerializer,
    }

    base_role = ProjectNoMember

    RBAC_BY_ACTION = {
        "list": ["workspace.project.list"],
        "retrieve": ["project.info.view"],
        "create": ["workspace.project.create"],
        "destroy": ["project.remove"],
        "update": ["project.info.edit"],
        "partial_update": ["project.info.edit"],
    }

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()

    def get_object_project(self):
        # no need to query project, because we are in a project view
        return self.current_object

    def get_object_workspace(self):
        return self.current_object.workspace

    def get_list_role(self, request, *args, **kwargs):
        # always return the lowest role with `workspace.project.list` permission when logged in
        return PublicViewer, None

    def get_create_role(self, request, *args, **kwargs):
        # The role for creating a Project is based on the payload
        # we read the 'workspace' short_uuid from the payload and determine the user role based on that
        workspace_suuid = request.data.get("workspace")
        try:
            workspace = Workspace.objects.get(short_uuid=workspace_suuid)
        except ObjectDoesNotExist:
            raise Http404
        return Membership.get_workspace_role(request.user, workspace)


class ProjectReadOnlyView(
    ProjectRoleMixin,
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Project.projects.active().select_related("workspace")
    serializer_class = ProjectSerializer
    lookup_field = "short_uuid"
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["workspace.project.list"],
    }

    def get_list_role(self, request, *args, **kwargs):
        # we read the workspace suuid from the url
        try:
            workspace = Workspace.objects.get(short_uuid=kwargs.get("parent_lookup_workspace__short_uuid"))
        except Workspace.DoesNotExist:
            raise Http404
        return Membership.get_workspace_role(request.user, workspace)
