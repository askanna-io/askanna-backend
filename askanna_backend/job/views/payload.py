# -*- coding: utf-8 -*-
import json
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.permissions import (
    ProjectMember,
    ProjectNoMember,
    RoleBasedPermission,
)
from core.views import ObjectRoleMixin
from job.models import JobPayload
from job.serializers import (
    JobPayloadSerializer,
)
from users.models import MSP_WORKSPACE


class JobPayloadView(
    ObjectRoleMixin,
    NestedViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = JobPayload.objects.filter(jobdef__deleted__isnull=True)
    lookup_field = "short_uuid"
    serializer_class = JobPayloadSerializer
    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
        "get_partial": ["project.run.list"],
    }

    def get_list_role(self, request, *args, **kwargs):
        # always return ProjectMember for logged in users since the listing always shows objects based on membership
        if request.user.is_anonymous:
            return ProjectNoMember, None
        return ProjectMember, None

    def get_object_project(self):
        return self.current_object.jobdef.project

    def get_object_workspace(self):
        return self.current_object.jobdef.project.workspace

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
                    Q(jobdef__project__workspace__visibility="PUBLIC")
                    & Q(jobdef__project__visibility="PUBLIC")
                )
            )

        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(jobdef__project__workspace__in=member_of_workspaces)
                | (
                    Q(jobdef__project__workspace__visibility="PUBLIC")
                    & Q(jobdef__project__visibility="PUBLIC")
                )
            )
        )

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