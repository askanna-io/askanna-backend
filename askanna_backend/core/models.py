import uuid

from django.db import models
from django_extensions.db.models import ActivatorModel, TimeStampedModel, TitleDescriptionModel


class DeletedModel(models.Model):
    """
    Defines an additional field to registere when the model is deleted
    """
    deleted = models.DateTimeField(blank=True, auto_now_add=False, auto_now=False)
    class Meta:
        abstract = True

class BaseModel(TitleDescriptionModel, TimeStampedModel, DeletedModel, models.Model):

    uuid = models.UUIDField(primary_key=True, db_index=True, editable=False, default=uuid.uuid4)
    short_uuid = models.CharField(max_length=32, blank=True)

    class Meta:
        abstract = True

class ActivatedModel(ActivatorModel, BaseModel):
    class Meta:
        abstract = True
