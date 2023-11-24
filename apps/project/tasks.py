from config.celery_app import app as celery_app

from core.utils.maintenance import remove_objects
from project.models import Project


@celery_app.task(name="project.tasks.delete_projects")
def delete_projects():
    """
    We delete projects that are marked to delete. Also we check whether we don't have a
    deletion for the parent Workspace. This will otherwise conflict with the Project deletion.

    We pass on the queryset to get all objects these will be filtered in the function remove_objects which will handle
    the deletion of the objects after checking the deletion delay.
    """
    remove_objects(
        Project.objects.filter(
            deleted_at__isnull=False,
            workspace__deleted_at__isnull=True,
        )
    )
