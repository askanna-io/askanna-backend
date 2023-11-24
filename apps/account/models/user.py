from __future__ import annotations

import uuid as _uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from account.models.membership import MSP_WORKSPACE, MemberProfile
from core.models import BaseModel
from core.permissions.role_utils import get_user_role, merge_role_permissions
from core.permissions.roles import AskAnnaAdmin, AskAnnaMember, AskAnnaPermissions
from workspace.models import Workspace


class User(MemberProfile, AbstractUser):
    uuid = models.UUIDField(db_index=True, editable=False, default=_uuid.uuid4, verbose_name="UUID")

    email = models.EmailField("Email address", blank=False)
    name = models.CharField("Name of User", blank=False, max_length=255)

    # We don't use the first and last name set by the AbstractUser
    first_name = None
    last_name = None

    objects = UserManager()

    def __str__(self):
        return f"{self.name or self.username} ({self.suuid})"

    def get_status(self) -> str:
        if self.is_active:
            return "active"
        return "blocked"

    def get_user_role(self) -> type[AskAnnaPermissions]:
        if self.is_superuser:
            return AskAnnaAdmin
        return AskAnnaMember

    @property
    def active_memberships(self):
        return self.memberships.active_members()

    def to_deleted(self):
        """
        We don't actually remove the user, we mark it as deleted and we remove the confidential info such as
        email, password and avatar files.

        Note: if the user has active workspace memberships, these memberships are not deleted. The memberships will be
        marked as deleted. If a membership was using the global profile, then the profile will be copied over to the
        membership before removing the user.
        """
        for membership in self.active_memberships:
            membership.to_deleted()

        self.auth_token.delete()
        self.set_unusable_password()

        self.is_active = False
        self.username = f"deleted-user-{self.suuid}"
        self.email = f"deleted-user-{self.suuid}@dev.null"
        self.name = "deleted user"
        self.job_title = ""

        self.delete_avatar_file()

        self.save(
            update_fields=[
                "is_active",
                "username",
                "email",
                "name",
                "job_title",
                "modified_at",
            ]
        )

        super().to_deleted()

    def request_has_object_read_permission(self, request, view) -> bool:
        # User can always read its own user as long as the user is active
        if request.user and request.user == self and self.is_active:
            return True

        # Workspace memberships can be set to use the user profile. Select all memberships that use this user profile.
        memberships_workspace_uuids = self.active_memberships.filter(
            use_global_profile=True, object_type=MSP_WORKSPACE
        ).values_list("object_uuid", flat=True)

        # Read permission to this user is given for PUBLIC workspaces where this user has a membership with the
        # profile set to use this user's profile
        if Workspace.objects.filter(uuid__in=memberships_workspace_uuids, visibility="PUBLIC").exists():
            return True

        if request.user.is_anonymous:
            return False

        # Read permission to this user is given for workspaces where this user has a membership with the profile set to
        # use this user profile and the request.user has an active membership with the role permission
        # "workspace.info.view"
        request_user_memberships = request.user.active_memberships.filter(object_uuid__in=memberships_workspace_uuids)

        request_user_roles = list({membership.get_role() for membership in request_user_memberships}) + [
            get_user_role(request.user)
        ]

        return merge_role_permissions(request_user_roles).get("workspace.info.view", False)


class PasswordResetLog(BaseModel):
    email = models.EmailField()
    user = models.ForeignKey("account.User", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    remote_ip = models.GenericIPAddressField("Remote IP", null=True)
    remote_host = models.CharField(max_length=1024, blank=True, default="")
    front_end_domain = models.CharField(max_length=1024, blank=True, default="")
    meta = models.JSONField(null=True, default=None)

    class Meta:
        ordering = ["-created_at"]
