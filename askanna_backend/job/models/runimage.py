from core.models import BaseModel
from django.db import models


class RunImage(BaseModel):
    """
    Store information about the Images we use for the runs
    """

    tag = models.CharField(max_length=128, null=True, blank=True, editable=False)
    digest = models.CharField(max_length=256, null=True, blank=True, editable=False)

    cached_image = models.CharField(max_length=256, null=True, blank=True, editable=False)

    @property
    def fullname(self):
        if self.tag:
            return f"{self.name}:{self.tag}"
        return self.name

    def __str__(self):
        return self.fullname

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "image",
            "suuid": self.suuid,
            "name": self.fullname,
            "tag": self.tag,
            "digest": self.digest,
        }

    class Meta:
        ordering = ["-created"]
