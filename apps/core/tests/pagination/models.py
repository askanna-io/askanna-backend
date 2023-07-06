from django.db import models

from core.models import BaseModel


class BaseCursorPaginationModel(BaseModel):
    idx = models.IntegerField()


class NullableCursorPaginationModel(BaseModel):
    idx = models.IntegerField(null=True)
