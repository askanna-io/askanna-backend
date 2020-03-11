from django.db import models

from django_extensions.db.models import ActivatorModel, TimeStampedModel, TitleDescriptionModel


class Project(ActivatorModel, TimeStampedModel, TitleDescriptionModel, models.Model):
    name = models.CharField(max_length=255)
    workspace = models.IntegerField(default=1)
