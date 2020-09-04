from django.contrib.auth.models import AbstractUser, Group
from django.db.models import CharField
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from core.models import BaseModel, SlimBaseModel, SlimBaseForAuthModel
import json


class User(SlimBaseForAuthModel, AbstractUser):

    # First Name and Last Name do not cover name patterns
    # around the globe.

    name = CharField(_("Name of User"), blank=True, max_length=255)

    def get_absolute_url(self):
        return reverse("users:detail", kwargs={"username": self.username})

    def get_name(self):
        return self.name or self.get_full_name() or self.username or self.short_uuid


MSP_PROJECT = "PR"
MSP_WORKSPACE = "WS"
MEMBERSHIPS = ((MSP_PROJECT, "Project"), (MSP_WORKSPACE, "Workspace"))
WS_MEMBER = "WM"
WS_ADMIN = "WA"
ROLES = ((WS_MEMBER, "member"), (WS_ADMIN, "admin"))


class Membership(SlimBaseModel):
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
        "users.User",
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
    )

    class Meta:
        indexes = [models.Index(fields=["user", "object_uuid"])]
        ordering = ["-created"]
        unique_together = [["user", "object_uuid"]]
