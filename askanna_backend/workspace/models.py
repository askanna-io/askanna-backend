from core.const import VISIBLITY
from core.models import AuthorModel, BaseModel
from django.db import models


class WorkspaceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)

    def inactive(self):
        return self.filter(deleted_at__isnull=False)


class WorkspaceManager(models.Manager):
    def get_queryset(self):
        return WorkspaceQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class Workspace(AuthorModel, BaseModel):
    name = models.CharField(max_length=255, blank=False, null=False, db_index=True, default="New workspace")
    visibility = models.CharField(max_length=10, choices=VISIBLITY, default="PRIVATE", db_index=True)

    objects = WorkspaceManager()

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
