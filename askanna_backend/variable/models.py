from core.models import SlimBaseModel
from django.db import models
from django.db.models import Q
from django_cryptography.fields import encrypt


class VariableQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted__isnull=True, project__deleted__isnull=True, project__workspace__deleted__isnull=True
        )

    def inactive(self):
        return self.filter(
            Q(deleted__isnull=False) | Q(project__deleted__isnull=True) | Q(project__workspace__deleted__isnull=False)
        )


class VariableManager(models.Manager):
    def get_queryset(self):
        return VariableQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def inactive(self):
        return self.get_queryset().inactive()


class Variable(SlimBaseModel):
    """Model to store Variables that can be used for runnings jobs"""

    name = models.CharField(max_length=128)
    value = encrypt(models.TextField(default=None, blank=True, null=True))
    is_masked = models.BooleanField(default=False)

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        to_field="uuid",
        related_name="variable",
    )

    objects = VariableManager()

    def get_value(self):
        if self.is_masked:
            return "***masked***"
        return self.value

    class Meta:
        ordering = ["-created"]
