from celery import shared_task

from core.utils.maintenance import remove_objects
from workspace.models import Workspace


@shared_task(name="workspace.tasks.delete_workspaces")
def delete_workspaces():
    """
    We delete workspaces that are marked to delete.

    We pass on the queryset to get all objects these will be filtered in the function remove_objects which will handle
    the deletion of the objects after checking the deletion delay.
    """

    remove_objects(
        Workspace.objects.filter(
            deleted_at__isnull=False,
        )
    )
