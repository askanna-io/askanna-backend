from core.utils.maintenance import remove_objects
from run.models import Run

from config.celery_app import app as celery_app


@celery_app.task(name="run.tasks.delete_runs")
def delete_runs():
    """
    We delete runs that are marked for deleted longer than 5 mins ago
    We also check for the condition where the `jobdef` (and higher in the hierarchy) is also not deleted
    Otherwise we would conflict the deletion operation
    """
    remove_objects(
        Run.objects.filter(
            jobdef__deleted_at__isnull=True,
            jobdef__project__deleted_at__isnull=True,
            jobdef__project__workspace__deleted_at__isnull=True,
        )
    )
