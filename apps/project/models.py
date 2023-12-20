from django.db import models

from core.models import AuthorModel, NameDescriptionBaseModel, VisibilityModel


class ProjectQuerySet(models.QuerySet):
    def active(self, add_select_related: bool = False):
        active_query = self.filter(deleted_at__isnull=True, workspace__deleted_at__isnull=True)

        if add_select_related is True:
            return active_query.select_related("workspace", "created_by_user", "created_by_member__user")

        return active_query


class Project(AuthorModel, VisibilityModel, NameDescriptionBaseModel):
    """A project resembles an organisation with code, jobs, runs artifacts"""

    name = models.CharField(max_length=255, blank=False, null=False, db_index=True, default="New project")

    workspace = models.ForeignKey("workspace.Workspace", on_delete=models.CASCADE)

    objects = ProjectQuerySet().as_manager()

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    @property
    def last_created_package(self):
        return self.packages.active().order_by("-created_at").first()

    @property
    def is_private(self) -> bool:
        return self.visibility == "PRIVATE" or self.workspace.is_private

    @property
    def is_public(self) -> bool:
        return self.visibility == "PUBLIC" and self.workspace.is_public

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name", "created_at"]),
        ]
