from django.db import models
from core.models import SlimBaseModel

# Create your models here.


class ProjectTemplate(SlimBaseModel):
    name = models.CharField(max_length=255)
    template_location = models.TextField()

    scope = models.ForeignKey(
        "workspace.Workspace", on_delete=models.SET_NULL, blank=True, null=True
    )
