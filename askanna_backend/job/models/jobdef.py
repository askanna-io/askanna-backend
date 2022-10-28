from core.models import BaseModel
from django.db import models


class JobQuerySet(models.QuerySet):
    def active_jobs(self):
        return self.filter(
            deleted__isnull=True,
            project__deleted__isnull=True,
            project__workspace__deleted__isnull=True,
        )

    def inactive_jobs(self):
        return self.filter(deleted__isnull=False)

    def active(self):
        """
        Only active jobs
        """
        return self.active_jobs()

    def inactive(self):
        """
        Inactive jobs only
        """
        return self.inactive_jobs()


class ActiveJobManager(models.Manager):
    def get_queryset(self):
        return JobQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class JobDef(BaseModel):
    """
    Consider this as the job registry storing the identity of the job itself.
    """

    objects = models.Manager()
    jobs = ActiveJobManager()

    project = models.ForeignKey("project.Project", on_delete=models.CASCADE, blank=True, null=True)

    environment_image = models.CharField(
        max_length=2048,
        null=True,
        blank=True,
        editable=False,
    )
    timezone = models.CharField(max_length=256, default="UTC")

    def get_name(self):
        return self.name

    def __str__(self):
        return f"{self.name} ({self.short_uuid})"

    @property
    def relation_to_json(self):
        return {
            "relation": "jobdef",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job definition"
