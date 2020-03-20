from django.db import models

from django_extensions.db.models import ActivatorModel, TimeStampedModel, TitleDescriptionModel


class BaseModel(ActivatorModel, TimeStampedModel, TitleDescriptionModel, models.Model):
    class Meta:
        abstract = True
