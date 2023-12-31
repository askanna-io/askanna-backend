from django.db import models
from django.db.models import Q

from core.const import VISIBLITY
from core.models import AuthorModel, NameDescriptionBaseModel


class ProjectQuerySet(models.QuerySet):
    def active(self):
        return self.filter(deleted_at__isnull=True, workspace__deleted_at__isnull=True)

    def inactive(self):
        return self.filter(Q(deleted_at__isnull=False) | Q(workspace__deleted_at__isnull=False))


class ProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class Project(AuthorModel, NameDescriptionBaseModel):
    """A project resembles an organisation with code, jobs, runs artifacts"""

    name = models.CharField(max_length=255, blank=False, null=False, db_index=True, default="New project")

    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE)
    visibility = models.CharField(max_length=10, choices=VISIBLITY, default="PRIVATE", db_index=True)

    objects = ProjectManager()

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    @property
    def last_created_package(self):
        return self.packages.active_and_finished().order_by("-created_at").first()

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
