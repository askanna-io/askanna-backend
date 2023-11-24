from django.db import models

from core.models import AuthorModel, NameDescriptionBaseModel, VisibilityModel


class WorkspaceQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True)


class Workspace(AuthorModel, VisibilityModel, NameDescriptionBaseModel):
    name = models.CharField(max_length=255, blank=False, null=False, db_index=True, default="New workspace")

    objects = WorkspaceQuerySet().as_manager()

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
