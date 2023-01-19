from core.utils.maintenance import remove_objects
from workspace.models import Workspace

from config.celery_app import app as celery_app


@celery_app.task(name="workspace.tasks.delete_workspaces")
def delete_workspaces():
    """
    We delete workspace that are marked for deleted
    We pass on the queryset to get all objects
    these will be filtered in the function remove_objects to delete ones
    """

    remove_objects(Workspace.objects.all())
