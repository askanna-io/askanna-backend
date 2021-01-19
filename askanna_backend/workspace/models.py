from core.models import ActivatedModel


class Workspace(ActivatedModel):
    def __str__(self):
        # FIXME: change title to name
        return self.title

    @property
    def relation_to_json(self):
        return {
            "name": self.title,
            "uuid": str(self.uuid),
            "short_uuid": self.short_uuid,
        }
