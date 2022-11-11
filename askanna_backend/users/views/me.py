import random
import string

from core.permissions import RoleBasedPermission
from core.views import SerializerByActionMixin
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from project.models import Project
from rest_framework.generics import DestroyAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import Membership
from users.serializers import (
    AvatarMeSerializer,
    GlobalMeSerializer,
    ObjectAvatarMeSerializer,
    ProjectMeSerializer,
    UpdateMeSerializer,
    UpdateObjectMeSerializer,
    WorkspaceMeSerializer,
)
from workspace.models import Workspace

User = get_user_model()


class BaseMeViewSet(
    NestedViewSetMixin,
    SerializerByActionMixin,
    DestroyAPIView,
    UpdateAPIView,
    RetrieveAPIView,
):
    serializer_class = GlobalMeSerializer
    permission_classes = [RoleBasedPermission]
    http_method_names = ["get", "patch", "delete"]

    serializer_classes_by_action = {
        "patch": UpdateMeSerializer,
    }

    RBAC_BY_ACTION = {
        "get": [
            "askanna.me",
        ],
        "delete": [
            "askanna.member",
        ],
        "patch": [
            "askanna.member",
        ],
    }

    def get_object_role(self, request, *args, **kwargs):
        return None

    def initial(self, request, *args, **kwargs):
        """
        Here we do a pre-initial call which sets the role of the user
        This was not possible in the standard Django middleware as DRF overwrites this with their own flow
        """
        # set the role and user_roles
        request.role = User.get_role(request)
        request.user_roles = [request.role]

        if getattr(self, "get_object_role"):
            object_role = self.get_object_role(request, *args, **kwargs)
            if object_role:
                request.user_roles.append(object_role)
                request.object_role = object_role

        super().initial(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """
        We don't actually remove the user, we just mark it as deleted
        """

        # set all memberships inactive for this deleted user
        for membership in Membership.objects.filter(user=instance):
            # setting the membership to deleted will automaticly read `use_global_profile`
            # to copy over some info from User object
            membership.to_deleted()

        instance.to_deleted()
        instance.is_active = False
        instance.username = "deleted-user-" + "".join(
            random.choices(string.ascii_uppercase + string.digits, k=6)  # nosec: B311
        )

        instance.name = "deleted user"
        instance.job_title = "deleted"
        instance.email = "deleted@dev.null"
        instance.save(
            update_fields=[
                "is_active",
                "modified",
                "name",
                "email",
                "username",
                "job_title",
            ]
        )

    def get_object(self):
        """
        Always return the current user as a viewpoint
        in the baseMeViewSet only
        """
        user = self.request.user
        if user.is_anonymous or user.is_active:
            return user
        # always raise a 404 when no active user is visiting this endpoint
        raise Http404


class MeAvatarViewSet(
    NestedViewSetMixin,
    DestroyAPIView,
    UpdateAPIView,
):
    serializer_class = AvatarMeSerializer
    http_method_names = ["patch", "delete"]

    permission_classes = [RoleBasedPermission]

    RBAC_BY_ACTION = {
        "delete": [
            "askanna.member",
        ],
        "patch": [
            "askanna.member",
        ],
    }

    def get_object_role(self, request, *args, **kwargs):
        return None

    def initial(self, request, *args, **kwargs):
        """
        Here we do a pre-initial call which sets the role of the user
        This was not possible in the standard Django middleware as DRF overwrites this with their own flow
        """
        # set the role and user_roles
        request.role = User.get_role(request)
        request.user_roles = [request.role]
        request.object_role = None

        if getattr(self, "get_object_role"):
            object_role = self.get_object_role(request, *args, **kwargs)
            if object_role:
                request.user_roles.append(object_role)
                request.object_role = object_role

        super().initial(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """
        We just delete the avatar, not the user
        After we install the default avatar for the user
        """
        instance.prune()
        instance.install_default_avatar()

    def get_object(self):
        """
        Always return the current user as a viewpoint
        in the baseMeViewSet only
        """
        user = self.request.user
        # if user.is_anonymous or user.is_active: #disabled untill public projects
        if user.is_active:
            return user
        # always raise a 404 when no active user is visiting this endpoint
        raise Http404


class ObjectMeViewSet(BaseMeViewSet):
    serializer_class = WorkspaceMeSerializer

    serializer_classes_by_action = {
        "patch": UpdateObjectMeSerializer,
    }

    RBAC_BY_ACTION = {
        "get": ["workspace.me.view", "project.me.view"],
        "delete": ["workspace.me.remove"],
        "patch": ["workspace.me.edit"],
    }

    def perform_destroy(self, instance):
        """
        We don't actually remove the membership, we just mark it as deleted

        - if `use_global_profile` was True, copy the information over from Profile (done via to_deleted)
        """
        instance.to_deleted()

    def _default_membership_for_public(self):
        # AskAnnaMember without this object membership
        # or Anonymous users will get a dummy membership
        guest_role = {
            "PR": "PN",  # project guest
            "WS": "WN",  # workspace guest
        }
        return Membership(
            **{
                "name": "Guest",
                "job_title": "Guest",
                "role": guest_role.get(self.current_object_type, "AN"),  # default to PublicViewer
                "user": None,
            }
        )

    def get_object(self):
        """
        Always return the current user's membership (WV, WM, WA, [PM, PA])
        Anonymous or non-members will get a dummy Membership
        At this point we have a valid and existing workspace/project to work with
        So we need to check membership only
        """
        user = self.request.user
        if user.is_active:
            try:
                membership = Membership.objects.get(
                    user=user,
                    object_uuid=self.current_object.uuid,
                    deleted__isnull=True,
                )
            except ObjectDoesNotExist:
                if self.current_object.visibility == "PUBLIC":
                    return self._default_membership_for_public()
                raise Http404
            return membership
        return self._default_membership_for_public()

    def get_object_role(self, request, *args, **kwargs):
        """
        To be executed before super().initial() in our custom initial
        - Setting current_object to Project/Workspace
        - Returning the role for the user for this request
        """
        object_role = None
        self.current_object = None
        self.current_object_type = kwargs.get("object_type")

        if kwargs.get("object_type") == "WS" and kwargs.get("suuid"):
            try:
                obj = Workspace.objects.get(suuid=kwargs.get("suuid"))
            except ObjectDoesNotExist:
                raise Http404
            self.current_object = obj

            if request.user.is_anonymous and self.current_object.visibility == "PRIVATE":
                # when the workspace is PRIVATE, raise a 404 NOT FOUND
                raise Http404

            object_role, request.membership = Membership.get_workspace_role(request.user, obj)

        if kwargs.get("object_type") == "PR" and kwargs.get("suuid"):
            try:
                obj = Project.objects.get(suuid=kwargs.get("suuid"))
            except ObjectDoesNotExist:
                raise Http404
            self.current_object = obj

            if request.user.is_anonymous and (
                self.current_object.visibility == "PRIVATE" or self.current_object.workspace.visibility == "PRIVATE"
            ):
                # when the workspace or project is PRIVATE, raise a 404 NOT FOUND
                raise Http404

            object_role, request.membership = Membership.get_project_role(request.user, obj)
            request.user_roles += Membership.get_roles_for_project(request.user, obj)

        return object_role


class ProjectMeViewSet(ObjectMeViewSet):
    serializer_class = ProjectMeSerializer

    def get_object(self):
        """
        Always return the current user's membership (WV, WM, WA, [PM, PA])
        Anonymous or non-members will get a dummy Membership
        At this point we have a valid and existing workspace/project to work with
        So we need to check membership only
        """
        user = self.request.user
        if user.is_active:
            try:
                workspace_membership = Membership.objects.get(
                    user=user,
                    object_uuid=self.current_object.workspace.uuid,
                    deleted__isnull=True,
                )
            except ObjectDoesNotExist:
                workspace_membership = None

            try:
                membership = Membership.objects.get(
                    user=user,
                    object_uuid=self.current_object.uuid,
                    deleted__isnull=True,
                )
            except ObjectDoesNotExist:
                if workspace_membership:
                    return workspace_membership
                if self.current_object.visibility == "PUBLIC":
                    return self._default_membership_for_public()
                raise Http404
            return membership
        return self._default_membership_for_public()


class ObjectAvatarMeViewSet(MeAvatarViewSet):
    serializer_class = ObjectAvatarMeSerializer

    def get_object_role(self, request, *args, **kwargs):
        """
        To be executed before super().initial() in our custom initial
        - Setting current_object to Project/Workspace
        """
        object_role = None
        self.current_object = None
        self.current_object_type = kwargs.get("object_type")

        if kwargs.get("object_type") == "WS" and kwargs.get("suuid"):
            try:
                obj = Workspace.objects.get(suuid=kwargs.get("suuid"))
            except ObjectDoesNotExist:
                raise Http404
            self.current_object = obj
            object_role, request.membership = Membership.get_workspace_role(request.user, obj)

        if kwargs.get("object_type") == "PR" and kwargs.get("suuid"):
            try:
                obj = Project.objects.get(suuid=kwargs.get("suuid"))
            except ObjectDoesNotExist:
                raise Http404
            self.current_object = obj
            object_role, request.membership = Membership.get_project_role(request.user, obj)

        return object_role

    def get_object(self):
        """
        Always return the current user's membership (WV, WM, WA, [PM, PA])
        Anonymous or non-members will get a dummy Membership
        At this point we have a valid and existing workspace/project to work with
        So we need to check membership only
        """
        user = self.request.user
        if user.is_active:
            try:
                membership = Membership.objects.get(
                    user=user,
                    object_uuid=self.current_object.uuid,
                    deleted__isnull=True,
                )
            except ObjectDoesNotExist:
                raise Http404
            return membership

        # AskAnnaMember without this object membership
        # or Anonymous users will get a dummy membership
        guest_role = {
            "PR": "PN",  # project guest
            "WS": "WN",  # workspace guest
        }
        return Membership(
            **{
                "name": "Guest",
                "job_title": "Guest",
                "role": guest_role.get(self.current_object_type, "AN"),  # default to PublicViewer
                "user": None,
            }
        )
