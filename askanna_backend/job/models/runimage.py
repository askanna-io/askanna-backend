from django.db import models

from core.models import NameDescriptionBaseModel


class RunImage(NameDescriptionBaseModel):
    """
    Store information about the Images we use for the runs
    """

    name = models.CharField(max_length=255, blank=False, null=False, editable=False, db_index=True)
    tag = models.CharField(max_length=128, blank=True, default="", editable=False)
    digest = models.CharField(max_length=256, blank=False, null=False, editable=False)

    cached_image = models.CharField(max_length=255, blank=True, default="")

    @property
    def fullname(self):
        # Check if last part of the name contains the tag, else add it
        if self.tag and not self.name.endswith(f":{self.tag}"):
            return f"{self.name}:{self.tag}"
        return self.name

    def __str__(self):
        return self.fullname

    def set_cached_image(self, cached_image):
        self.cached_image = cached_image
        self.save(
            update_fields=[
                "cached_image",
                "modified_at",
            ]
        )

    def unset_cached_image(self):
        self.cached_image = ""
        self.save(
            update_fields=[
                "cached_image",
                "modified_at",
            ]
        )

    class Meta:
        ordering = ["-created_at"]
        unique_together = ["name", "tag", "digest"]
