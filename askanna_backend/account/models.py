from __future__ import annotations

import datetime
import os
from typing import List, Optional, Type, Union

from account.signals import avatar_changed_signal
from core.models import SlimBaseForAuthModel, SlimBaseModel
from core.permissions.askanna_roles import (
    AskAnnaAdmin,
    AskAnnaMember,
    AskAnnaPublicViewer,
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    ProjectPublicViewer,
    ProjectViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceNoMember,
    WorkspacePublicViewer,
    WorkspaceViewer,
    get_role_class,
)
from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from project.models import Project
from workspace.models import Workspace


class BaseAvatarModel:

    avatar_specs = {
        "icon": (60, 60),
        "small": (120, 120),
        "medium": (180, 180),
        "large": (240, 240),
    }

    def install_default_avatar(self):
        self.write(
            open(
                settings.RESOURCES_DIR.path(settings.USERPROFILE_DEFAULT_AVATAR),
                "rb",
            )
        )

    def delete_avatar(self):
        """
        Remove existing avatars from the system for this user.
        And install default avatar
        """
        self.prune()
        self.install_default_avatar()

    def stored_path_with_name(self, name) -> str:
        filename = "avatar_{}_{}.png".format(self.uuid.hex, name)
        return os.path.join(settings.AVATARS_ROOT, self.storage_location, filename)

    def storage_location_with_name(self, name) -> str:
        filename = "avatar_{}_{}.png".format(self.uuid.hex, name)
        return os.path.join(self.storage_location, filename)

    @property
    def storage_location(self) -> str:
        return os.path.join(
            self.uuid.hex,
        )

    @property
    def stored_path(self) -> str:
        return os.path.join(settings.AVATARS_ROOT, self.storage_location, self.filename)

    @property
    def filename(self) -> str:
        return "avatar_{}.image".format(self.uuid.hex)

    def prune(self):
        for spec_name, spec_size in self.avatar_specs.items():
            filename = self.stored_path_with_name(spec_name)
            try:
                os.remove(filename)
            except (FileNotFoundError, Exception) as e:
                print(e, type(e))

        try:
            os.remove(self.stored_path)
        except (FileNotFoundError, Exception) as e:
            print(e, type(e))

    @property
    def read(self) -> bytes:
        """
        Read the avatar from filesystem
        """

        with open(self.stored_path, "rb") as f:
            return f.read()

    def write(self, stream):
        """
        Write contents to the filesystem, as is without changing image format
        """
        os.makedirs(os.path.join(settings.AVATARS_ROOT, self.storage_location), exist_ok=True)
        with open(self.stored_path, "wb") as f:
            f.write(stream.read())

        avatar_changed_signal.send(sender=self.__class__, instance=self)

    def prepend_cdn_url(self, location: str) -> str:
        return "{BASE_URL}/files/avatars/{LOCATION}".format(BASE_URL=settings.ASKANNA_CDN_URL, LOCATION=location)

    def append_timestamp_to_url(self, location: str) -> str:
        timestamp = datetime.datetime.timestamp(self.modified)
        return "{location}?{timestamp}".format(location=location, timestamp=timestamp)

    @property
    def avatar_cdn_locations(self) -> dict:
        return dict(
            zip(
                self.avatar_specs.keys(),
                [
                    self.append_timestamp_to_url(self.prepend_cdn_url(self.storage_location_with_name(f)))
                    for f in self.avatar_specs.keys()
                ],
            )
        )


class User(BaseAvatarModel, SlimBaseForAuthModel, AbstractUser):
    email = models.EmailField("Email address", blank=False)
    name = models.CharField("Name of User", blank=False, max_length=255)
    job_title = models.CharField("Job title", blank=True, default="", max_length=255)

    # First and last name do not cover name patterns around the glob and are removed from the AbstractUser model
    first_name = None
    last_name = None

    objects = UserManager()

    @property
    def memberships(self):
        return self.memberships

    @property
    def auth_token(self):
        return self.auth_token

    @classmethod
    def get_role(cls, request):  # TODO: rename to get_askanna_role
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
        for membership in self.memberships.filter(deleted__isnull=True):
            membership.to_deleted()

        self.delete_avatar()
        self.auth_token.delete()

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
                "modified",
            ]
        )

        super().to_deleted()


MSP_PROJECT = "PR"
MSP_WORKSPACE = "WS"
MEMBERSHIPS = ((MSP_PROJECT, "Project"), (MSP_WORKSPACE, "Workspace"))
WS_MEMBER = "WM"
WS_ADMIN = "WA"
WS_VIEWER = "WV"
ROLES = ((WS_VIEWER, "viewer"), (WS_MEMBER, "member"), (WS_ADMIN, "admin"))


class MemberQuerySet(models.QuerySet):
    def active_members(self):
        return self.filter(deleted__isnull=True)

    def admins(self):
        return self.active_members().filter(role=WS_ADMIN)

    def members(self):
        """
        Members include admins
        """
        return self.active_members()

    def all_admins(self):
        return self.filter(role=WS_ADMIN)

    def all_members(self):
        return self.filter(role=WS_MEMBER)


class ActiveMemberManager(models.Manager):
    def get_queryset(self):
        return MemberQuerySet(self.model, using=self._db)

    def admins(self):
        return self.get_queryset().admins()

    def members(self):
        return self.get_queryset().members()


class Membership(BaseAvatarModel, SlimBaseModel):
    """
    Membership holds the relation between
    - workspace vs user
    - project vs user

    README: We don't choose to work with Django generic relations for now

    """

    object_uuid = models.UUIDField(db_index=True)
    object_type = models.CharField(max_length=2, choices=MEMBERSHIPS)
    role = models.CharField(max_length=2, default=WS_MEMBER, choices=ROLES)
    user = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
        blank=True,
        null=True,
    )

    use_global_profile = models.BooleanField(
        "Use AskAnna profile",
        default=True,
        help_text="Use information from the global user account",
    )
    name = models.CharField("Name", blank=True, max_length=255)
    job_title = models.CharField("Job title", blank=True, max_length=255)

    objects = models.Manager()
    members = ActiveMemberManager()

    @property
    def workspace(self):
        if self.object_type == MSP_WORKSPACE:
            return Workspace.objects.get(uuid=self.object_uuid)

    def get_status(self):
        if self.user and not self.deleted:
            return "active"
        if self.deleted:
            return "deleted"
        if getattr(self, "invitation", None):
            return "invited"
        return "blocked"

    def get_role(
        self,
    ) -> Union[
        Type[WorkspaceAdmin],
        Type[WorkspaceMember],
        Type[WorkspaceViewer],
        Type[ProjectAdmin],
        Type[ProjectMember],
        Type[ProjectViewer],
    ]:
        return get_role_class(self.role)

    @classmethod
    def get_roles_for_project(
        cls, user, project
    ) -> List[
        Union[
            Type[ProjectAdmin],
            Type[ProjectMember],
            Type[ProjectViewer],
            Type[ProjectNoMember],
            Type[ProjectPublicViewer],
            Type[WorkspaceAdmin],
            Type[WorkspaceMember],
            Type[WorkspaceViewer],
            Type[WorkspaceNoMember],
            Type[WorkspacePublicViewer],
        ]
    ]:
        workspace_role = cls.get_workspace_role(user, project.workspace)
        project_role = cls.get_project_role(user, project)
        roles = [workspace_role, project_role]

        if workspace_role.code == "WA" and ProjectAdmin not in roles:
            roles.append(ProjectAdmin)
        elif workspace_role.code == "WM" and ProjectMember not in roles:
            roles.append(ProjectMember)
        elif workspace_role.code == "WV" and ProjectViewer not in roles:
            roles.append(ProjectViewer)

        # Clean up the roles list. If multiple Project roles are present, remove the "lower" ones.
        if ProjectNoMember in roles and any(r in roles for r in [ProjectAdmin, ProjectMember, ProjectViewer]):
            roles.remove(ProjectNoMember)
        if ProjectAdmin in roles and ProjectMember in roles:
            roles.remove(ProjectMember)
        if ProjectAdmin in roles and ProjectViewer in roles:
            roles.remove(ProjectViewer)
        if ProjectMember in roles and ProjectViewer in roles:
            roles.remove(ProjectViewer)

        return roles

    @classmethod
    def get_project_membership(cls, user, project: Project) -> Optional[Membership]:
        try:
            membership = cls.objects.get(
                object_uuid=str(project.uuid),
                object_type="PR",
                user=user,
                deleted__isnull=True,
            )
        except ObjectDoesNotExist:
            return None
        else:
            return membership

    @classmethod
    def get_project_role(
        cls, user, project: Project
    ) -> Union[
        Type[ProjectAdmin], Type[ProjectMember], Type[ProjectViewer], Type[ProjectNoMember], Type[ProjectPublicViewer]
    ]:
        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PRIVATE" or project.workspace.visibility == "PRIVATE"
        ):
            return ProjectNoMember

        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PUBLIC" and project.workspace.visibility == "PUBLIC"
        ):
            return ProjectPublicViewer

        membership = cls.get_project_membership(user, project)
        if membership:
            return membership.get_role()
        elif project.visibility == "PUBLIC" and project.workspace.visibility == "PUBLIC":
            return ProjectPublicViewer

        return ProjectNoMember

    @classmethod
    def get_workspace_membership(cls, user, workspace: Workspace) -> Optional[Membership]:
        try:
            membership = cls.objects.get(
                object_uuid=str(workspace.uuid),
                object_type="WS",
                user=user,
                deleted__isnull=True,
            )
        except ObjectDoesNotExist:
            return None
        else:
            return membership

    @classmethod
    def get_workspace_role(
        cls, user, workspace: Workspace
    ) -> Union[
        Type[WorkspaceAdmin],
        Type[WorkspaceMember],
        Type[WorkspaceViewer],
        Type[WorkspaceNoMember],
        Type[WorkspacePublicViewer],
    ]:
        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PRIVATE":
            return WorkspaceNoMember
        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PUBLIC":
            return WorkspacePublicViewer

        membership = cls.get_workspace_membership(user, workspace)
        if membership:
            return membership.get_role()
        elif workspace.visibility == "PUBLIC":
            return WorkspacePublicViewer

        return WorkspaceNoMember

    def get_role_serialized(self):
        """
        Role to be exposed to the outside
        """
        role = self.get_role()
        return {
            "code": role.code,
            "name": role.name,
        }

    def __str__(self):
        if self.get_name():
            return f"{self.get_name()} ({self.suuid})"
        return self.suuid

    def get_name(self):
        """
        Get name, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.name
        return self.name

    def get_job_title(self):
        """
        Get job_title, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.job_title
        return self.job_title

    def get_avatar(self):
        """
        Get avatar, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.avatar_cdn_locations
        return self.avatar_cdn_locations

    def to_deleted(self):
        if self.use_global_profile and self.user:
            # If use_global_profile is True, then make a copy of the global profile to the membership profile.
            self.name = self.user.name
            self.job_title = self.user.job_title
            self.use_global_profile = False
            self.save(update_fields=["name", "job_title", "use_global_profile", "modified"])

            # Copy the avatar from the user to membership
            self.write(open(self.user.stored_path, "rb"))

        super().to_deleted()

    class Meta:
        ordering = ["-created"]
        unique_together = [["user", "object_uuid", "object_type", "deleted"]]


class UserProfile(Membership):
    """For now, the UserProfile extends the Membership model and contains the same information as the Membership."""

    pass


class Invitation(Membership):
    email = models.EmailField(blank=False)

    @property
    def token_signer(self):
        return signing.TimestampSigner()

    def generate_token(self):
        return self.token_signer.sign(self.suuid)


class PasswordResetLog(SlimBaseModel):
    email = models.EmailField()
    user = models.ForeignKey("account.User", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    remote_ip = models.GenericIPAddressField("Remote IP", null=True)
    remote_host = models.CharField(max_length=1024, null=True, default=None)
    front_end_domain = models.CharField(max_length=1024, null=True, default=None)
    meta = models.JSONField(null=True, default=None)

    class Meta:
        ordering = ["-created"]
