from core.const import VISIBLITY
from core.models import ActivatorModel, AuthorModel, BaseModel
from django.db import models


class ProjectQuerySet(models.QuerySet):
    def active_projects(self):
        return self.filter(
            deleted__isnull=True,
            workspace__deleted__isnull=True,
        )

    def inactive_projects(self):
        return self.filter(deleted__isnull=False)

    def active(self):
        """
        Only active projects
        """
        return self.active_projects()

    def inactive(self):
        """
        Inactive projects only
        """
        return self.inactive_projects()


class ActiveProjectManager(models.Manager):
    def get_queryset(self):
        return ProjectQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class Project(AuthorModel, ActivatorModel, BaseModel):
    """A project resembles an organisation with code, jobs, runs artifacts"""

    objects = models.Manager()
    projects = ActiveProjectManager()

    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE, blank=True, null=True)

    visibility = models.CharField(max_length=10, choices=VISIBLITY, default="PRIVATE", db_index=True)

    def get_name(self):
        return None or self.name

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.short_uuid})"
        return self.short_uuid

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "project",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["name"]
