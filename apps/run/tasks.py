from celery import shared_task

from core.utils.maintenance import remove_objects
from run.models import Run
from run.utils import (
    update_run_metrics_file_and_meta as _update_run_metrics_file_and_meta,
)
from run.utils import (
    update_run_variables_file_and_meta as _update_run_variables_file_and_meta,
)


@shared_task(name="run.tasks.update_run_metrics_file_and_meta", bind=True)
def update_run_metrics_file_and_meta(self, run_suuid: str):
    """
    Update the metrics file, and meta information with count and unique metric_names and label_names
    """
    run = Run.objects.get(suuid=run_suuid)

    try:
        _update_run_metrics_file_and_meta(run)
    except AssertionError as exc:
        self.retry(countdown=15, max_retries=5, exc=exc)


@shared_task(name="run.tasks.update_run_variables_file_and_meta", bind=True)
def update_run_variables_file_and_meta(self, run_suuid: str):
    """
    Update the variables file, and meta information with count and unique variable_names and label_names
    """
    run = Run.objects.get(suuid=run_suuid)

    try:
        _update_run_variables_file_and_meta(run)
    except AssertionError as exc:
        self.retry(countdown=15, max_retries=5, exc=exc)


@shared_task(name="run.tasks.delete_runs")
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
