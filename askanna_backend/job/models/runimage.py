# -*- coding: utf-8 -*-
from django.db import models

from core.models import BaseModel


class RunImage(BaseModel):
    """
    Store information about the Images we use for the runs
    """

    tag = models.CharField(max_length=128, null=True, blank=True, editable=False)
    digest = models.CharField(max_length=256, null=True, blank=True, editable=False)

    cached_image = models.CharField(
        max_length=256, null=True, blank=True, editable=False
    )

    @property
    def fullname(self):
        name = self.name
        if self.tag:
            name += ":" + self.tag
        return name

    class Meta:
        ordering = ["-created"]
        verbose_name = "Run image"
        verbose_name_plural = "Run images"
