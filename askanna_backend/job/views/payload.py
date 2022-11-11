from core.permissions import ProjectMember, ProjectNoMember, RoleBasedPermission
from core.views import ObjectRoleMixin
from django.db.models import Q
from job.models import JobPayload
from job.serializers import JobPayloadSerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import MSP_WORKSPACE


class JobPayloadView(
    ObjectRoleMixin,
    NestedViewSetMixin,
    viewsets.ReadOnlyModelViewSet,
):
    """List payloads"""

    queryset = JobPayload.objects.filter(jobdef__deleted__isnull=True)
    lookup_field = "suuid"
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
                .filter(Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE).values_list("object_uuid", flat=True)

        return (
            super()
            .get_queryset()
            .filter(
                Q(jobdef__project__workspace__in=member_of_workspaces)
                | (Q(jobdef__project__workspace__visibility="PUBLIC") & Q(jobdef__project__visibility="PUBLIC"))
            )
        )

    # overwrite the default view and serializer for detail page
    # We will retrieve the original sent payload from the filesystem and serve as JSON
    def retrieve(self, request, *args, **kwargs):
        """Get the payload content

        Note: this request will not result in an payload information object, but it will actually retrieve the payload
        itselves.
        """
        instance = self.get_object()

        if instance:
            return Response(instance.payload)

        return Response({"message_type": "error", "message": "Payload was not found"}, status=404)
