from core.filters import OrderingFilter
from core.mixins import ObjectRoleMixin
from core.permissions.role import RoleBasedPermission
from django.db.models import Q
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from job.models import JobPayload
from job.serializers import JobPayloadSerializer
from rest_framework import mixins, viewsets
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from run.models import Run
from users.models import MSP_WORKSPACE, Membership


class JobPayloadView(
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """List payloads"""

    queryset = JobPayload.objects.active()
    lookup_field = "suuid"
    serializer_class = JobPayloadSerializer
    permission_classes = [RoleBasedPermission]
    filter_backends = [OrderingFilter]
    ordering_fields = [
        "created",
        "modified",
    ]

    rbac_permissions_by_action = {
        "list": ["project.run.list"],
        "retrieve": ["project.run.list"],
    }

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

    def get_object_project(self):
        return self.current_object.jobdef.project

    def get_parrent_roles(self, request, *args, **kwargs):
        run_suuid = self.kwargs["parent_lookup_run__suuid"]
        try:
            run = Run.objects.active().get(suuid=run_suuid)
        except Run.DoesNotExist:
            raise Http404

        return Membership.get_roles_for_project(request.user, run.jobdef.project)

    @extend_schema(responses={200: OpenApiTypes.OBJECT})
    def retrieve(self, request, *args, **kwargs):
        """Get the payload content

        Note: this request will not result in an payload information object, but it will actually retrieve the payload
        itselves.
        """
        instance = self.get_object()

        if instance:
            return Response(instance.payload)

        return Response({"detail": "Payload was not found"}, status=404)
