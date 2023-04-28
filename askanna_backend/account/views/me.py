from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from account.models.membership import Membership
from account.serializers.me import (
    MeAvatarSerializer,
    MeSerializer,
    ProjectMeSerializer,
    WorkspaceMeAvatarSerializer,
    WorkspaceMeSerializer,
)
from core.mixins import (
    ObjectRoleMixin,
    PartialUpdateModelMixin,
    UpdateModelWithoutPartialUpateMixin,
)
from core.permissions.role import RoleBasedPermission
from project.models import Project
from workspace.models import Workspace


class MeMixin(
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def perform_destroy(self, instance):
        instance.to_deleted()


class AvatarMixin(
    UpdateModelWithoutPartialUpateMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    def perform_destroy(self, instance):
        instance.delete_avatar()

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        return Response(status=status.HTTP_204_NO_CONTENT, data=None)


class GlobalMeMixin(ObjectRoleMixin):
    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "retrieve": ["askanna.me"],
        "update": ["askanna.me.edit"],
        "partial_update": ["askanna.me.edit"],
        "destroy": ["askanna.me.remove"],
    }

    def get_object(self):
        """
        Return the current user as the object for this view. If the user is not active, raise HTTP status code 404.
        """
        user = self.request.user
        if user.is_anonymous or user.is_active:
            return user
        raise Http404


class WorkspaceMeMixin(ObjectRoleMixin):
    permission_classes = [RoleBasedPermission]
    rbac_permissions_by_action = {
        "retrieve": ["workspace.me.view"],
        "update": ["workspace.me.edit"],
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


@extend_schema_view(
    retrieve=extend_schema(description="Get info from the authenticated account"),
    partial_update=extend_schema(description="Update the authenticated account info"),
    destroy=extend_schema(description="Remove the authenticated account from the platform"),
)
class MeViewSet(GlobalMeMixin, MeMixin):
    serializer_class = MeSerializer


@extend_schema_view(
    retrieve=extend_schema(description="Get info from the authenticated account in relation to a workspace"),
    partial_update=extend_schema(description="Update the authenticated account workspace's membership info"),
    destroy=extend_schema(description="Remove the authenticated account workspace's membership"),
)
class WorkspaceMeViewSet(
    WorkspaceMeMixin,
    MeMixin,
):
    serializer_class = WorkspaceMeSerializer


@extend_schema_view(
    retrieve=extend_schema(description="Get info from the authenticated account in relation to a project"),
)
class ProjectMeViewSet(
    ObjectRoleMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = ProjectMeSerializer

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


@extend_schema_view(
    update=extend_schema(description="Update the avatar of the authenticated account", responses={204: None}),
    destroy=extend_schema(description="Remove the avatar of the authenticated account"),
)
class MeAvatarViewSet(
    GlobalMeMixin,
    AvatarMixin,
):
    serializer_class = MeAvatarSerializer
    rbac_permissions_by_action = {
        "update": ["askanna.me.edit"],
        "destroy": ["askanna.me.edit"],
    }


@extend_schema_view(
    update=extend_schema(
        description="Update the avatar of the authenticated account workspace's membership", responses={204: None}
    ),
    destroy=extend_schema(description="Remove the avatar of the authenticated account workspace's membership"),
)
class WorkspaceMeAvatarViewSet(
    WorkspaceMeMixin,
    AvatarMixin,
):
    serializer_class = WorkspaceMeAvatarSerializer
    rbac_permissions_by_action = {
        "update": ["workspace.me.edit"],
        "destroy": ["workspace.me.edit"],
    }
