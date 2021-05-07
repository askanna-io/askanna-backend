from core.models import ActivatedModel


class Workspace(ActivatedModel):
    def get_name(self):
        return self.name

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
