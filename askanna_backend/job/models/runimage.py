from core.models import BaseModel
from django.db import models


class RunImage(BaseModel):
    """
    Store information about the Images we use for the runs
    """

    name = models.CharField(max_length=255, blank=False, null=False, editable=False, db_index=True)
    tag = models.CharField(max_length=128, blank=True, default="", editable=False)
    digest = models.CharField(max_length=256, blank=False, null=False, editable=False)

    cached_image = models.CharField(max_length=255, blank=True, default="")

    @property
    def fullname(self):
        if self.tag:
            return f"{self.name}:{self.tag}"
        return self.name

    def __str__(self):
        return self.fullname

    def set_cached_image(self, cached_image):
        self.cached_image = cached_image
        self.save(update_fields=["cached_image", "modified"])

    def unset_cached_image(self):
        self.cached_image = ""
        self.save(update_fields=["cached_image", "modified"])

    class Meta:
        ordering = ["-created"]
        unique_together = ["name", "tag", "digest"]
