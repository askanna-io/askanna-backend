import datetime
import os
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.fields import JSONField

from django.db.models import CharField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from core.models import SlimBaseModel, SlimBaseForAuthModel

from users.signals import avatar_changed_signal


class User(SlimBaseForAuthModel, AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.

    name = CharField(_("Name of User"), blank=True, max_length=255)
    front_end_domain = models.CharField(max_length=1024, null=True, default=None)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def get_name(self):
        return self.name or self.get_full_name() or self.username or self.short_uuid

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
ROLES = ((WS_MEMBER, "member"), (WS_ADMIN, "admin"))


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


class Membership(SlimBaseModel):
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

    avatar_specs = {
        "icon": (60, 60),
        "small": (120, 120),
        "medium": (180, 180),
        "large": (240, 240),
    }

    def install_default_avatar(self):
        self.write(
            open(
                settings.RESOURCES_DIR.path(settings.USERPROFILE_DEFAULT_AVATAR), "rb",
            )
        )

    def delete_avatar(self):
        """
        Remove existing avatars from the system for this user.
        And install default avatar
        """
        self.prune()

    def stored_path_with_name(self, name):
        filename = "avatar_{}_{}.png".format(self.uuid.hex, name)
        return os.path.join(settings.AVATARS_ROOT, self.storage_location, filename)

    def storage_location_with_name(self, name):
        filename = "avatar_{}_{}.png".format(self.uuid.hex, name)
        return os.path.join(self.storage_location, filename)

    @property
    def storage_location(self):
        return os.path.join(self.uuid.hex,)

    @property
    def stored_path(self):
        return os.path.join(settings.AVATARS_ROOT, self.storage_location, self.filename)

    @property
    def filename(self):
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
    def read(self):
        """
            Read the avatar from filesystem
        """

        with open(self.stored_path, "rb") as f:
            return f.read()

    def write(self, stream):
        """
            Write contents to the filesystem, as is without changing image format
        """
        os.makedirs(
            os.path.join(settings.AVATARS_ROOT, self.storage_location), exist_ok=True
        )
        with open(self.stored_path, "wb") as f:
            f.write(stream.read())

        avatar_changed_signal.send(sender=self.__class__, instance=self)

    def prepend_cdn_url(self, location):
        return "{BASE_URL}/files/avatars/{LOCATION}".format(
            BASE_URL=settings.ASKANNA_CDN_URL, LOCATION=location
        )

    def append_timestamp_to_url(self, location):
        timestamp = datetime.datetime.timestamp(self.modified)
        return "{location}?{timestamp}".format(location=location, timestamp=timestamp)

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
            "avatar": dict(
                zip(
                    self.avatar_specs.keys(),
                    [
                        self.append_timestamp_to_url(
                            self.prepend_cdn_url(self.storage_location_with_name(f))
                        )
                        for f in self.avatar_specs.keys()
                    ],
                )
            ),
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
        }

    def get_name(self):
        """
        If the membership name is set, return this otherwise return the users name
        """
        if self.name:
            return self.name
        if self.user:
            return self.user.get_name()
        return ""

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
    user = models.ForeignKey(
        "users.User", blank=True, null=True, default=None, on_delete=models.SET_NULL
    )
    remote_ip = models.GenericIPAddressField(_("Remote IP"), null=True)
    remote_host = models.CharField(max_length=1024, null=True, default=None)
    front_end_domain = models.CharField(max_length=1024, null=True, default=None)
    meta = JSONField(null=True, default=None)

    class Meta:
        ordering = ["-created"]
