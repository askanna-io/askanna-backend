from core.const import VISIBLITY
from core.models import ActivatedModel, AuthorModel
from django.db import models


class Workspace(AuthorModel, ActivatedModel):

    visibility = models.CharField(max_length=10, choices=VISIBLITY, default="PRIVATE", db_index=True)

    def get_name(self):
        return None or self.name

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.suuid})"
        return self.suuid

    @property
    def relation_to_json(self):
        """
        Used for the serializer to trace back to this instance
        """
        return {
            "relation": "workspace",
            "suuid": self.suuid,
            "name": self.get_name(),
        }
