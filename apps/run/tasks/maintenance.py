from config.celery_app import app as celery_app

from core.utils.maintenance import remove_objects
from run.models import Run


@celery_app.task(name="run.tasks.delete_runs")
def delete_runs():
    """
    We delete runs that are marked to delete. Also check for the condition where the Job (and higher in the
    hierarchy) or Package is also not deleted. This will otherwise conflict with the Run deletion.

    We pass on the queryset to get all objects these will be filtered in the function remove_objects which will handle
    the deletion of the objects after checking the deletion delay.
    """
    remove_objects(
        Run.objects.filter(
            deleted_at__isnull=False,
            jobdef__deleted_at__isnull=True,
            jobdef__project__deleted_at__isnull=True,
            jobdef__project__workspace__deleted_at__isnull=True,
            package__deleted_at__isnull=True,
        )
    )
