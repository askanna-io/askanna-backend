# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import ActivatedModel


class Workspace(ActivatedModel):
    def get_name(self):
        return self.name

    visibility = models.CharField(
        _("Visibility"), max_length=255, default="PRIVATE", db_index=True
    )

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "workspace",
            "name": self.get_name(),
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }
