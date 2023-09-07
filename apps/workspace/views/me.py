from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view

from account.models.membership import Membership
from account.serializers.me import MembershipMeSerializer
from account.views.me import MeMixin
from workspace.models import Workspace


@extend_schema_view(
    retrieve=extend_schema(description="Get info from the authenticated account in relation to a workspace"),
    partial_update=extend_schema(description="Update the authenticated account workspace's membership info"),
    destroy=extend_schema(description="Remove the authenticated account workspace's membership"),
)
class WorkspaceMeViewSet(MeMixin):
    serializer_class = MembershipMeSerializer
    rbac_permissions_by_action = {
        "retrieve": ["workspace.me.view"],
        "partial_update": ["workspace.me.edit"],
        "destroy": ["workspace.me.remove"],
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
                    "role": "WP",
                }
            )

        return Membership(
            **{
                "suuid": None,
                "user": self.request.user,
                "use_global_profile": True,
                "role": "WP",
            }
        )

    def get_object(self):
        """
        Return the request user's membership for the requested workspace. If the user does not have a membership and
        the workspace visibility is PUBLIC, we return the default role WorkspacePublicViewer.
        """
        if self.request.user.is_active:
            try:
                return Membership.objects.get(
                    user=self.request.user,
                    object_uuid=self.request_workspace.uuid,
                    deleted_at__isnull=True,
                )
            except ObjectDoesNotExist:
                pass

        if self.request_workspace.visibility == "PRIVATE":
            raise Http404

        return self._default_membership_for_public()

    def get_parrent_roles(self, request):
        try:
            self.request_workspace = Workspace.objects.get(suuid=self.kwargs.get("suuid"))
        except ObjectDoesNotExist as exc:
            raise Http404 from exc

        return [self.get_workspace_role(request.user, self.request_workspace)]
