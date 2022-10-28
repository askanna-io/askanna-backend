from job.mailer import send_run_notification as do_send_notification
from job.models import JobDef
from package.models import Package
from run.models import Run

from config.celery_app import app as celery_app


@celery_app.task(bind=True, name="job.tasks.send_run_notification")
def send_run_notification(self, run_uuid):
    print(f"Received message to send notifications for run {run_uuid}")

    # get the run
    run = Run.objects.get(pk=run_uuid)

    package = run.package
    configyml = package.get_askanna_config()
    if configyml is None:
        # we could not parse the config
        return

    job_config = configyml.jobs.get(run.jobdef.name)
    if job_config and job_config.notifications:
        # only send notifications when notifications are configured
        # for this job and globally (infered in the job notifications)
        do_send_notification(run.status, run=run, job=job_config)


@celery_app.task(bind=True, name="job.tasks.send_missed_schedule_notification")
def send_missed_schedule_notification(self, job_uuid):
    print(f"Received message to send notifications for missed schedule {job_uuid}")

    # get the job
    job = JobDef.objects.get(pk=job_uuid)

    # get latest package for the job
    # Fetch the latest package found in the job.project
    package = Package.objects.filter(finished__isnull=False).filter(project=job.project).order_by("-created").first()
    configyml = package.get_askanna_config()
    if configyml is None:
        # we could not parse the config
        return

    job_config = configyml.jobs.get(job.name)
    if job_config and job_config.notifications:
        # only send notifications when notifications are configured
        # for this job and globally (infered in the job notifications)
        do_send_notification(
            "SCHEDULE_MISSED",
            job=job_config,
            extra_vars={
                "project": job.project,
                "jobdef": job,
            },
        )
