# -*- coding: utf-8 -*-
import datetime
import os
import typing

from core.models import SlimBaseForAuthModel, SlimBaseModel
from core.permissions import (
    AskAnnaAdmin,
    AskAnnaMember,
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    PublicViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceNoMember,
    WorkspaceViewer,
)
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _
from users.signals import avatar_changed_signal


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

    # First Name and Last Name do not cover name patterns
    # around the globe.

    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    job_title = models.CharField(_("Job title"), blank=True, max_length=255)
    front_end_domain = models.CharField(max_length=1024, null=True, default=None)

    def get_name(self):
        return self.name or self.username or self.short_uuid

    @classmethod
    def get_role(self, request):
        # defaulting the role to `PublicViewer` when no match is found
        # key: is_anonymous, is_active, is_superuser
        roles = {
            (1, 0, 0): PublicViewer,
            (0, 1, 1): AskAnnaAdmin,
            (0, 1, 0): AskAnnaMember,
        }
        return roles.get(
            (
                request.user.is_anonymous,
                request.user.is_active,
                request.user.is_superuser,
            ),
            PublicViewer,
        )

    @property
    def relation_to_json_with_avatar(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "user",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
            "avatar": self.avatar_cdn_locations(),
        }

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "user",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }


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

    objects = models.Manager()
    members = ActiveMemberManager()

    object_uuid = models.UUIDField(db_index=True)
    object_type = models.CharField(max_length=2, choices=MEMBERSHIPS)
    role = models.CharField(max_length=2, default=WS_MEMBER, choices=ROLES)
    job_title = models.CharField(_("Job title"), blank=True, max_length=255)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
        blank=True,
        null=True,
    )
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    use_global_profile = models.BooleanField(
        _("Use AskAnna profile"),
        default=True,
        help_text=_("Use information from the global AskAnna profile"),
    )

    def get_role(self):
        mapping = {
            "WA": WorkspaceAdmin,
            "WM": WorkspaceMember,
            "WV": WorkspaceViewer,
            "PA": ProjectAdmin,
            "PM": ProjectMember,
            "AN": PublicViewer,
        }
        return mapping.get(self.role, PublicViewer)

    @classmethod
    def get_roles_for_project(cls, user, project) -> typing.List:
        roles = []
        workspace_role, _ = cls.get_workspace_role(user, project.workspace)
        project_role, _ = cls.get_project_role(user, project)
        roles = [workspace_role, project_role]
        if workspace_role.code == "WA":
            roles.append(ProjectAdmin)
        if workspace_role.code == "WM":
            roles.append(ProjectMember)
        return roles

    @classmethod
    def get_project_role(cls, user, project=None):
        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PRIVATE" or project.workspace.visibility == "PRIVATE"
        ):
            return ProjectNoMember, None

        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PUBLIC" and project.workspace.visibility == "PUBLIC"
        ):
            return PublicViewer, None

        try:
            membership = cls.objects.get(
                object_uuid=str(project.uuid),
                object_type="PR",
                user=user,
                deleted__isnull=True,  # don't retrieve invalid memberships
            )
        except ObjectDoesNotExist:
            # we have an AskAnnaMember/AskAnnaAdmin but no membership
            if project.visibility == "PUBLIC":
                return PublicViewer, None
            return ProjectNoMember, None

        return membership.get_role(), membership

    @classmethod
    def get_workspace_role(cls, user, workspace=None):
        # this method is used in the `.initial` method in ViewSets of:
        # - workspace
        # - project
        # - job
        # - run
        # - run-releted objects
        # defaulting the membershiprole to `WorkspaceNoMember` when no match is found

        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PRIVATE":
            return WorkspaceNoMember, None
        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PUBLIC":
            return PublicViewer, None

        try:
            membership = cls.objects.get(
                object_uuid=str(workspace.uuid),
                object_type="WS",
                user=user,
                deleted__isnull=True,  # don't retrieve invalid memberships
            )
        except ObjectDoesNotExist:
            # we have an AskAnnaMember/AskAnnaAdmin but no membership
            if workspace.visibility == "PUBLIC":
                # this overrides, when the workspace is set to public, the user
                # without a membership becomes PublicViewer
                return PublicViewer, None
            return WorkspaceNoMember, None

        return membership.get_role(), membership

    def get_role_serialized(self):
        """
        Role to be exposed to the outside
        """
        roles = {
            "WA": WorkspaceAdmin,
            "WV": WorkspaceViewer,
            "WM": WorkspaceMember,
            "PA": ProjectAdmin,
            "PM": ProjectMember,
        }
        role = roles.get(self.role, PublicViewer)
        return {
            "name": role.name,
            "code": role.code,
        }

    def get_status(self):
        if self.user:
            return "accepted"
        return "invited"

    @property
    def relation_to_json_with_avatar(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "membership",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
            "avatar": self.get_avatar(),
            "job_title": self.get_job_title(),
            "role": self.get_role_serialized(),
            "status": self.get_status(),
        }

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "membership",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
            "job_title": self.get_job_title(),
            "role": self.get_role_serialized(),
            "status": self.get_status(),
        }

    def __str__(self):
        if self.get_name():
            return f"{self.get_name()} ({self.short_uuid})"
        return self.short_uuid

    def get_name(self):
        """
        Get name, respecting the `use_global_profile` setting
        FIXME: in Membership.get_name we omit the `use_global_profile=False` when:
        - Membership.name is ""/None
        - User.get_name() is returned instead (introducing a tertiary fallback)
        In the future get this fallbacks straight and explainable.
        """
        if self.use_global_profile and self.user:
            return self.user.get_name()
        if self.name:
            return self.name
        if self.user:
            return self.user.get_name()
        return ""  # no name set

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
            return self.user.avatar_cdn_locations()
        return self.avatar_cdn_locations()

    def to_deleted(self):
        super().to_deleted()

        if self.use_global_profile:
            # make snapshot of the membership profile if
            # we use_global_profile.
            self.name = self.user.get_name()
            self.job_title = self.user.job_title
            self.use_global_profile = False
            # copy the avatar from the user to membership
            self.write(open(self.user.stored_path, "rb"))
            self.save(update_fields=["name", "job_title", "use_global_profile"])

    class Meta:
        ordering = ["-created"]
        unique_together = [["user", "object_uuid", "object_type", "deleted"]]


class UserProfile(Membership):
    """For now, the userprofile contains the same information as the Membership.
    This UserProfile model extends the Membership model"""

    pass


class Invitation(Membership):
    email = models.EmailField(blank=False)
    front_end_url = models.URLField()


class PasswordResetLog(SlimBaseModel):
    email = models.EmailField()
    user = models.ForeignKey("users.User", blank=True, null=True, default=None, on_delete=models.SET_NULL)
    remote_ip = models.GenericIPAddressField(_("Remote IP"), null=True)
    remote_host = models.CharField(max_length=1024, null=True, default=None)
    front_end_domain = models.CharField(max_length=1024, null=True, default=None)
    meta = models.JSONField(null=True, default=None)

    class Meta:
        ordering = ["-created"]
