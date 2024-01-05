from django.db import models
from django.db.models import Q
from django_cryptography.fields import encrypt

from core.models import BaseModel


class VariableQuerySet(models.QuerySet):
    def active(self):
        return self.filter(
            deleted_at__isnull=True, project__deleted_at__isnull=True, project__workspace__deleted_at__isnull=True
        )

    def inactive(self):
        return self.filter(
            Q(deleted_at__isnull=False)
            | Q(project__deleted_at__isnull=False)
            | Q(project__workspace__deleted_at__isnull=False)
        )


class Variable(BaseModel):
    """Model to store Variables that can be used for runnings jobs"""

    name = models.CharField(max_length=128)
    value = encrypt(models.TextField(default=None, blank=True, null=True))
    is_masked = models.BooleanField(default=False)

    project = models.ForeignKey(
        "project.Project",
        on_delete=models.CASCADE,
        to_field="uuid",
        related_name="variables",
    )

    objects = VariableQuerySet().as_manager()

    def get_value(self):
        if self.is_masked:
            return "***masked***"
        return self.value

    class Meta:
        ordering = ["-created_at"]
