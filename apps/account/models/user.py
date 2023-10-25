from __future__ import annotations

import uuid as _uuid

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from account.models.avatar import BaseAvatarModel
from core.models import BaseModel
from core.permissions.askanna_roles import (
    AskAnnaAdmin,
    AskAnnaMember,
    AskAnnaPermissions,
    AskAnnaPublicViewer,
)


class User(BaseAvatarModel, AbstractUser):
    uuid = models.UUIDField(db_index=True, editable=False, default=_uuid.uuid4, verbose_name="UUID")

    email = models.EmailField("Email address", blank=False)
    name = models.CharField("Name of User", blank=False, max_length=255)
    job_title = models.CharField("Job title", blank=True, default="", max_length=255)

    # First and last name do not cover name patterns around the glob and are removed from the AbstractUser model
    first_name = None
    last_name = None

    objects = UserManager()

    def get_status(self) -> str:
        if self.is_active:
            return "active"
        return "blocked"

    def get_user_role(self) -> type[AskAnnaPermissions]:
        if self.is_superuser:
            return AskAnnaAdmin
        return AskAnnaMember

    @classmethod
    def get_role(cls, request) -> type[AskAnnaPermissions]:
        """
        Defaulting the role to `AskAnnaPublicViewer` when no match is found
        # key: is_anonymous, is_active, is_superuser
        """
        user_role_mapping = {
            (1, 0, 0): AskAnnaPublicViewer,
            (0, 1, 0): AskAnnaMember,
            (0, 1, 1): AskAnnaAdmin,
        }

        return user_role_mapping.get(
            (
                request.user.is_anonymous,
                request.user.is_active,
                request.user.is_superuser,
            ),
            AskAnnaPublicViewer,
        )

    def to_deleted(self):
        """
        We don't actually remove the user, we mark it as deleted and we remove the confidential info such as
        username and email.

        Note: if the user has active workspace memberships, these memberships are not deleted. The memberships will be
        marked as deleted. If a membership was using the global profile, then the profile will be copied over to the
        membership before removing the user.
        """
        for membership in self.memberships.filter(deleted_at__isnull=True):
            membership.to_deleted()

        self.delete_avatar()
        self.auth_token.delete()
        self.set_unusable_password()

        self.is_active = False
        self.username = f"deleted-user-{self.suuid}"
        self.email = f"deleted-user-{self.suuid}@dev.null"
        self.name = "deleted user"
        self.job_title = ""
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


class PasswordResetLog(BaseModel):
    email = models.EmailField()
    user = models.ForeignKey("account.User", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    remote_ip = models.GenericIPAddressField("Remote IP", null=True)
    remote_host = models.CharField(max_length=1024, blank=True, default="")
    front_end_domain = models.CharField(max_length=1024, blank=True, default="")
    meta = models.JSONField(null=True, default=None)

    class Meta:
        ordering = ["-created_at"]
