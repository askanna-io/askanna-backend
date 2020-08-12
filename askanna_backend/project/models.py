from django.db import models

from core.models import ActivatorModel, SlimBaseModel, DescriptionModel


class Project(ActivatorModel, DescriptionModel, SlimBaseModel):
    name = models.CharField(max_length=255)
    workspace = models.ForeignKey(
        "workspace.Workspace", on_delete=models.SET_NULL, blank=True, null=True
    )

    def __str__(self):
        return " - ".join([self.name, str(self.uuid)])

    class Meta:
        ordering = ["name"]

