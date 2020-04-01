from core.models import BaseModel, ActivatedModel

class Workspace(ActivatedModel):
    def __str__(self):
        return self.title

