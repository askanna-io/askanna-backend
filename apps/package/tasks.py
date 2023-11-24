from config.celery_app import app as celery_app

from core.utils.maintenance import remove_objects
from package.models import Package


@celery_app.task(name="package.tasks.delete_packages")
def delete_packages():
    """
    We delete packages that are marked to delete. Also we check whether we don't have a deletion for the parent
    Project and/or Workspace. This will otherwise conflict with the Pacakge deletion.

    We pass on the queryset to get all objects these will be filtered in the function remove_objects which will handle
    the deletion of the objects after checking the deletion delay.
    """
    remove_objects(
        Package.objects.filter(
            deleted_at__isnull=False,
            project__deleted_at__isnull=True,
            project__workspace__deleted_at__isnull=True,
        )
    )
