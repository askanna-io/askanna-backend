from django.db import models

from core.models import ActivatorModel, SlimBaseModel, DescriptionModel, AuthorModel


class ProjectQuerySet(models.QuerySet):
    def active_projects(self):
        return self.filter(deleted__isnull=True)

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


class Project(AuthorModel, ActivatorModel, DescriptionModel, SlimBaseModel):
    """A project resembles an organisation with code, jobs, runs artifacts
    """

    objects = models.Manager()
    projects = ActiveProjectManager()

    name = models.CharField(max_length=255)
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.SET_NULL, blank=True, null=True
    )

    template = models.UUIDField(db_index=True, editable=False, null=True)

    def __str__(self):
        return " - ".join([self.name, str(self.uuid)])

    @property
    def relation_to_json(self):
        return {
            "name": self.name,
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["name"]

