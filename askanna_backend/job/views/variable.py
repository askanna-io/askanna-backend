# -*- coding: utf-8 -*-
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import SerializerByActionMixin, ObjectRoleMixin
from core.views import workspace_to_project_role
from core.permissions import ProjectNoMember, ProjectMember, RoleBasedPermission

from job.models import (
    JobVariable,
    JobDef,
)
from job.serializers import (
    JobVariableSerializer,
    JobVariableCreateSerializer,
    JobVariableUpdateSerializer,
)

from project.models import Project
from users.models import MSP_WORKSPACE, Membership


class JobVariableView(
    ObjectRoleMixin,
    SerializerByActionMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.UpdateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobVariable.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobVariableSerializer

    filter_backends = (OrderingFilter, DjangoFilterBackend)
    ordering = ["project__name", "name"]
    ordering_fields = ["name", "project__name"]

    permission_classes = [RoleBasedPermission]
    RBAC_BY_ACTION = {
        "list": ["project.variable.list"],
        "retrieve": ["project.variable.list"],
        "create": ["project.variable.create"],
        "destroy": ["project.variable.remove"],
        "update": ["project.variable.edit"],
        "partial_update": ["project.variable.edit"],
    }

    serializer_classes_by_action = {
        "post": JobVariableCreateSerializer,
        "put": JobVariableUpdateSerializer,
        "patch": JobVariableUpdateSerializer,
    }

    def get_object_workspace(self):
        return self.current_object.project.workspace

    def get_object_project(self):
        return self.current_object.project

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        project = None
        if kwargs.get("parent_lookup_project__short_uuid"):
            project = Project.objects.get(
                short_uuid=kwargs.get("parent_lookup_project__short_uuid")
            )
        elif kwargs.get("parent_lookup_job_suuid"):
            job = JobDef.objects.get(short_uuid=kwargs.get("parent_lookup_job_suuid"))
            project = job.project
        if project:
            request.user_roles += Membership.get_roles_for_project(
                request.user, project
            )

        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_create_role(self, request, *args, **kwargs):
        parents = self.get_parents_query_dict()
        project_suuid = parents.get("project__short_uuid") or request.data.get(
            "project"
        )
        try:
            project = Project.objects.get(short_uuid=project_suuid)
        except ObjectDoesNotExist:
            raise Http404

        workspace_role, request.membership = Membership.get_workspace_role(
            request.user, project.workspace
        )
        request.user_roles.append(workspace_role)
        request.object_role = workspace_role

        # try setting a project role based on workspace role
        if workspace_to_project_role(workspace_role) is not None:
            inherited_role = workspace_to_project_role(workspace_role)
            request.user_roles.append(inherited_role)

        return Membership.get_project_role(request.user, project)

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        """
        Set default request.data in case we need this
        """
        project_suuid = None
        parents = self.get_parents_query_dict()
        if self.request.method.upper() in ["PUT", "PATCH"]:
            if hasattr(request.data, "_mutable"):
                setattr(request.data, "_mutable", True)
            if parents.get("project__short_uuid"):
                project_suuid = parents.get("project__short_uuid")
                request.data.update({"project": project_suuid})

            if not project_suuid:
                """
                Determine the project id by getting it from the object requested
                """
                variable = self.get_object()
                project_suuid = variable.project.short_uuid
                request.data.update({"project": project_suuid})

            if hasattr(request.data, "_mutable"):
                setattr(request.data, "_mutable", False)

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(project__workspace__visibility="PUBLIC")
                    & Q(project__visibility="PUBLIC")
                )
                .order_by("name")
            )

        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(project__workspace__in=member_of_workspaces)
                | (
                    Q(project__workspace__visibility="PUBLIC")
                    & Q(project__visibility="PUBLIC")
                )
            )
            .order_by("name")
        )
