# -*- coding: utf-8 -*-
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.views import PermissionByActionMixin
from job.filters import RunVariablesFilter
from job.models import RunVariableRow, RunVariables
from job.permissions import (
    IsMemberOfJobDefAttributePermission,
    IsMemberOfJobRunAttributePermission,
)
from job.serializers import RunVariableRowSerializer, RunVariablesSerializer
from project.models import Project
from users.models import MSP_WORKSPACE


class RunVariablesView(
    PermissionByActionMixin,
    NestedViewSetMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # we removed 'put' from the http_method_names as we don't suppor this in this view
    # - post and delete
    http_method_names = ["get", "patch", "head", "options", "trace"]

    queryset = RunVariables.objects.all()
    lookup_field = "jobrun__short_uuid"  # not needed for listviews
    serializer_class = RunVariablesSerializer

    permission_classes = [
        IsMemberOfJobRunAttributePermission,
    ]

    permission_classes_by_action = {
        "update": [IsMemberOfJobRunAttributePermission],
    }

    # Override because we don't return the full object, just the `variables` field
    def update(self, request, *args, **kwargs):
        _ = kwargs.pop("partial", False)
        instance = self.get_object()

        parent = instance.jobrun
        for permission in [IsMemberOfJobDefAttributePermission()]:
            if not permission.has_object_permission(
                request=self.request, view=self, obj=parent
            ):
                self.permission_denied(
                    self.request, message=getattr(permission, "message", None)
                )

        instance.variables = request.data.get("variables", [])
        instance.save()

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        instance.refresh_from_db()
        return Response(instance.variables)

    @action(detail=True, methods=["get"])
    def meta(self, request, *args, **kwargs):
        instance = self.get_object()

        special_labels = ["source"]
        if "is_masked" in instance.jobrun.variable_labels:
            special_labels.append("is_masked")

        response = {
            "suuid": instance.short_uuid,
            "project": instance.jobrun.jobdef.project.relation_to_json,
            "workspace": instance.jobrun.jobdef.project.workspace.relation_to_json,
            "job": instance.jobrun.jobdef.relation_to_json,
            "run": instance.jobrun.relation_to_json,
            "size": instance.size,
            "count": instance.count,
            "labels": special_labels
            + list(set(instance.jobrun.variable_labels) - set(special_labels)),
            "created": instance.created,
            "modified": instance.modified,
        }
        return Response(response)


class RunVariableRowView(
    PermissionByActionMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = RunVariableRow.objects.all()
    lookup_field = "short_uuid"  # not needed for listviews
    serializer_class = RunVariableRowSerializer

    # Override default, remove OrderingFilter because we use the DjangoFilterBackend version
    filter_backends = (DjangoFilterBackend,)

    filterset_class = RunVariablesFilter

    permission_classes = [
        IsMemberOfJobRunAttributePermission,
    ]

    permission_classes_by_action = {
        "list": [IsMemberOfJobRunAttributePermission],
        "create": [IsMemberOfJobRunAttributePermission],
        "update": [IsMemberOfJobRunAttributePermission],
    }

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
        member_of_projects = Project.objects.filter(
            workspace_id__in=member_of_workspaces
        ).values_list("short_uuid", flat=True)[
            ::-1
        ]  # hard convert to list for cross db query
        return queryset.filter(project_suuid__in=member_of_projects)
