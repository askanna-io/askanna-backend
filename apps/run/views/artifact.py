from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins

from account.models.membership import MSP_WORKSPACE
from core.mixins import PartialUpdateModelMixin
from core.permissions import AskAnnaPermissionByAction
from core.viewsets import AskAnnaGenericViewSet
from run.models import RunArtifact
from run.serializers.artifact import RunArtifactSerializerWithFileList


@extend_schema_view(
    retrieve=extend_schema(
        summary="Get run artifact info",
        description=(
            "Retrieve information about a run artifact. This includes the artifact meta data, download info and a "
            "list of files that are part of the artifact."
        ),
    ),
    partial_update=extend_schema(
        summary="Update run artifact info",
        description="Update the run artifact's `description`.",
    ),
)
class RunArtifactView(
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    AskAnnaGenericViewSet,
):
    """
    Retrieve information about a run's artifact and update the artifact's info.

    Note: creating a run artifact is implemented in the `RunView` and the list of a run's artifacts is part of the
    run's serializer.
    """

    queryset = RunArtifact.objects.active(add_select_related=True)

    permission_classes = [AskAnnaPermissionByAction]

    serializer_class = RunArtifactSerializerWithFileList

    def get_queryset(self):
        """
        Return only values from projects where the user is member of or has access to because it's public.
        """
        if self.request.user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )

        member_of_workspaces = self.request.user.memberships.filter(object_type=MSP_WORKSPACE).values_list(
            "object_uuid", flat=True
        )

        return (
            super()
            .get_queryset()
            .filter(
                Q(run__jobdef__project__workspace__in=member_of_workspaces)
                | (
                    Q(run__jobdef__project__workspace__visibility="PUBLIC")
                    & Q(run__jobdef__project__visibility="PUBLIC")
                )
            )
        )
