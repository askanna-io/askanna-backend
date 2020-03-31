from django.db import models

from core.models import ActivatedModel


class Project(ActivatedModel):
    name = models.CharField(max_length=255)
    workspace = models.IntegerField(default=1)

    def __str__(self):
        return " - ".join([self.name, str(self.uuid)])