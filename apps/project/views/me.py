from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins

from account.models.membership import Membership
from account.serializers.me import MembershipMeSerializer
from core.mixins import ObjectRoleMixin
from core.permissions.askanna import RoleBasedPermission
from core.viewsets import AskAnnaGenericViewSet
from project.models import Project


@extend_schema_view(
    retrieve=extend_schema(description="Get info from the authenticated account in relation to a project"),
)
class ProjectMeViewSet(
    ObjectRoleMixin,
    mixins.RetrieveModelMixin,
    AskAnnaGenericViewSet,
):
    serializer_class = MembershipMeSerializer

    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "retrieve": ["project.me.view"],
    }

    def _default_membership_for_public(self):
        if self.request.user.is_anonymous:
            return Membership(
                **{
                    "suuid": None,
                    "user": None,
                    "name": None,
                    "job_title": None,
                    "use_global_profile": None,
                    "role": "PP",
                }
            )

        return Membership(
            **{
                "suuid": None,
                "user": self.request.user,
                "use_global_profile": True,
                "role": "PP",
            }
        )

    def get_object(self):
        """
        Return the request user's membership for the requested project. If the user does not have a membership and
        the workspace & project visibility is PUBLIC, we return the default role ProjectPublicViewer.
        """
        if self.request.user.is_active:
            try:
                return Membership.objects.get(
                    user=self.request.user,
                    object_uuid=self.request_project.uuid,
                    deleted_at__isnull=True,
                )
            except ObjectDoesNotExist:
                pass

            # In case user does not have project membership, but has workspace membership, we return that membership
            try:
                return Membership.objects.get(
                    user=self.request.user,
                    object_uuid=self.request_project.workspace.uuid,
                    deleted_at__isnull=True,
                )
            except ObjectDoesNotExist:
                pass

        if self.request_project.visibility == "PRIVATE" or self.request_project.workspace.visibility == "PRIVATE":
            raise Http404

        return self._default_membership_for_public()

    def get_parrent_roles(self, request):
        try:
            self.request_project = Project.objects.get(suuid=self.kwargs.get("suuid"))
        except ObjectDoesNotExist as exc:
            raise Http404 from exc

        return self.get_roles_for_project(request.user, self.request_project)
