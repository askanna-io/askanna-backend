import logging

from config.celery_app import app as celery_app

from job.mailer import send_run_notification as do_send_notification
from job.models import JobDef
from package.models import Package
from run.models import Run

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="job.tasks.send_run_notification")
def send_run_notification(self, run_uuid):
    # Get the run
    run = Run.objects.get(pk=run_uuid)
    logger.info(f"Received message to send notifications for run {run.suuid}")

    package = run.package
    config_yml = package.get_askanna_config()
    if config_yml is None:
        logger.warning(f"Cannot send notifcations. No job config found for run {run.suuid}.")
        return

    job_config = config_yml.jobs.get(run.jobdef.name)
    if job_config and job_config.notifications:
        # only send notifications when notifications are configured
        # for this job and globally (infered in the job notifications)
        do_send_notification(run.status, run=run, job_config=job_config)
    else:
        logger.info(f"No notifications configured for run {run.suuid}.")


@celery_app.task(bind=True, name="job.tasks.send_missed_schedule_notification")
def send_missed_schedule_notification(self, job_uuid):
    # Get the job
    job = JobDef.objects.get(pk=job_uuid)
    logger.info(f"Received message to send notifications for missed schedule for job {job.suuid}")

    # Get latest package for the job
    # Fetch the latest package found in the job.project
    package = Package.objects.active_and_finished().filter(project=job.project).order_by("-created_at").first()
    if package is None:
        logger.warning(f"Cannot send notifcations. No package found for job {job.suuid}.")
        return
    config_yml = package.get_askanna_config()
    if config_yml is None:
        logger.warning(f"Cannot send notifcations. No config found for job {job.suuid}.")
        return

    job_config = config_yml.jobs.get(job.name)
    if job_config and job_config.notifications:
        # only send notifications when notifications are configured
        # for this job and globally (infered in the job notifications)
        do_send_notification("SCHEDULE_MISSED", job=job, job_config=job_config)
    else:
        logger.info(f"No notifications configured for job {job.suuid}.")
