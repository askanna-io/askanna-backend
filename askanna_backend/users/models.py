from django.contrib.auth.models import AbstractUser, Group
from django.contrib.postgres.fields import JSONField

from django.db.models import CharField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from core.models import BaseModel, SlimBaseModel, SlimBaseForAuthModel


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
        return self.name or self.user.get_name()

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
