# -*- coding: utf-8 -*-
import json
import os

from django.http import HttpResponse, JsonResponse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.mixins import HybridUUIDMixin
from core.views import (
    PermissionByActionMixin,
    SerializerByActionMixin,
)
from job.models import (
    JobDef,
    JobPayload,
    JobVariable,
)
from job.permissions import IsMemberOfProjectBasedOnPayload
from job.permissions import (
    IsMemberOfJobDefAttributePermission,
    IsMemberOfProjectAttributePermission,
)
from job.serializers import (
    JobPayloadSerializer,
    JobSerializer,
    JobVariableSerializer,
    JobVariableCreateSerializer,
    JobVariableUpdateSerializer,
)
from job.signals import artifact_upload_finish
from users.models import MSP_WORKSPACE

from .artifact import (  # noqa: F401
    JobArtifactView,
    JobArtifactShortcutView,
    ChunkedArtifactViewSet,
)
from .metrics import RunMetricsRowView, RunMetricsView  # noqa: F401
from .newrun import StartJobView  # noqa: F401
from .result import (  # noqa: F401
    RunStatusView,
    RunResultView,
    RunOutputView,
    ChunkedJobOutputViewSet,
)
from .runs import JobRunView, JobJobRunView  # noqa: F401
from .runvariables import RunVariableRowView, RunVariablesView  # noqa: F401


class JobActionView(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return queryset.filter(project__workspace__in=member_of_workspaces)


class JobPayloadView(NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = JobPayload.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobPayloadSerializer
    permission_classes = [IsMemberOfJobDefAttributePermission]

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return queryset.filter(jobdef__project__workspace__in=member_of_workspaces)

    # overwrite the default view and serializer for detail page
    # We will retrieve the original sent payload from the filesystem and serve as JSON
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance:
            return Response(instance.payload)

        return Response(
            {"message_type": "error", "message": "Payload was not found"}, status=404
        )

    @action(detail=True, methods=["get"], name="Get partial payload")
    def get_partial(self, request, *args, **kwargs):
        """
        Slice the payload with offset+limit lines

        offset: defaults to 0
        limit: defaults to 500
        """
        offset = request.query_params.get("offset", 0)
        limit = request.query_params.get("limit", 500)

        instance = self.get_object()

        limit_or_offset = request.query_params.get("limit") or request.query_params.get(
            "offset"
        )
        if limit_or_offset:
            offset = int(offset)
            limit = int(limit)
            json_obj = json.dumps(instance.payload, indent=1).splitlines(keepends=False)
            lines = json_obj[offset : offset + limit]
            return HttpResponse("\n".join(lines), content_type="application/json")
        return JsonResponse(instance.payload)


class ProjectJobViewSet(
    HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet
):
    """
    This is a duplicated viewset like `JobActionView` but ReadOnly version
    """

    queryset = JobDef.objects.all()
    lookup_field = "short_uuid"
    serializer_class = JobSerializer
    permission_classes = [IsMemberOfProjectAttributePermission]

    def get_queryset(self):
        """
        For listings return only values from projects
        where the current user had access to
        meaning also beeing part of a certain workspace
        """
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return queryset.filter(project__workspace__in=member_of_workspaces)


class JobVariableView(
    PermissionByActionMixin,
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

    permission_classes = [
        IsAuthenticated,
    ]

    permission_classes_by_action = {
        "list": [IsAuthenticated | IsAdminUser],
        "create": [IsAuthenticated, IsMemberOfProjectBasedOnPayload | IsAdminUser],
        "update": [IsAuthenticated, IsMemberOfProjectBasedOnPayload | IsAdminUser],
        "partial_update": [
            IsAuthenticated,
            IsMemberOfProjectBasedOnPayload | IsAdminUser,
        ],
    }

    serializer_classes_by_action = {
        "post": JobVariableCreateSerializer,
        "put": JobVariableUpdateSerializer,
        "patch": JobVariableUpdateSerializer,
    }

    def initial(self, request, *args, **kwargs):
        """
        Set default request.data in case we need this
        """
        project_suuid = None
        super().initial(request, *args, **kwargs)
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
        queryset = super().get_queryset()
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)
        return queryset.filter(project__workspace__in=member_of_workspaces)
