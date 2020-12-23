from core.models import ActivatedModel


class Workspace(ActivatedModel):
    def __str__(self):
        return self.title

