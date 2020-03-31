import uuid

from .utils import GoogleTokenGenerator, bx_decode

from django.db import models
from django_extensions.db.models import ActivatorModel, TimeStampedModel, TitleDescriptionModel


class DeletedModel(models.Model):
    """
    Defines an additional field to registere when the model is deleted
    """
    deleted = models.DateTimeField(blank=True, auto_now_add=False, auto_now=False, null=True)
    class Meta:
        abstract = True

class SlimBaseModel(TimeStampedModel, DeletedModel, models.Model):

    uuid = models.UUIDField(primary_key=True, db_index=True, editable=False, default=uuid.uuid4)
    short_uuid = models.CharField(max_length=32, blank=True)

    def save(self, *args, **kwargs):
        # Manually set the uuid and short_uuid
        if not self.uuid:
            self.uuid = uuid.uuid4()
        if not self.short_uuid and self.uuid:
            # FIXME: mode this part of code outside save to check for potential collision in existing set
            google_token = GoogleTokenGenerator()
            self.short_uuid = google_token.create_token(key='', uuid=self.uuid)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True

class BaseModel(TitleDescriptionModel, SlimBaseModel):
    class Meta:
        abstract = True
        ordering = ['-modified']

class ActivatedModel(ActivatorModel, BaseModel):
    class Meta:
        abstract = True
