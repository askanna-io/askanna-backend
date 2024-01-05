import logging

from celery import shared_task

from job.mailer import send_notification
from job.models import JobDef
from run.models import Run

logger = logging.getLogger(__name__)


@shared_task(name="job.tasks.send_run_notification")
def send_run_notification(run_suuid):
    logger.info(f"Received message to send notifications for run {run_suuid}.")

    run = Run.objects.get(suuid=run_suuid)

    package = run.package
    if package is None:
        logger.warning(f"Cannot send notifcations. No package found for run {run.suuid}.")
        return

    config_yml = package.get_askanna_config() if package else None
    if config_yml is None:
        logger.warning(f"Cannot send notifcations. No job config found for run {run.suuid}.")
        return

    job_config = config_yml.jobs.get(run.jobdef.name)
    if job_config and job_config.notifications:
        send_notification(run.status, run=run, job_config=job_config)
    else:
        logger.info(f"No notifications configured for run {run.suuid}.")


@shared_task(name="job.tasks.send_missed_schedule_notification")
def send_missed_schedule_notification(job_suuid):
    logger.info(f"Received message to send notifications for missed schedule for job {job_suuid}.")

    job = JobDef.objects.get(suuid=job_suuid)

    package = job.project.last_created_package
    if package is None:
        logger.warning(f"Cannot send notifcations. No package found for job {job.suuid}.")
        return

    config_yml = package.get_askanna_config()
    if config_yml is None:
        logger.warning(f"Cannot send notifcations. No config found for job {job.suuid}.")
        return

    job_config = config_yml.jobs.get(job.name)
    if job_config and job_config.notifications:
        send_notification("SCHEDULE_MISSED", job=job, job_config=job_config)
    else:
        logger.info(f"No notifications configured for job {job.suuid}.")
