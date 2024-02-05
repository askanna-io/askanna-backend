import datetime

from celery import shared_task
from django.db import transaction

from config import celery_app

from job.models import ScheduledJob
from package.models import Package
from run.models import Run


@shared_task(name="job.tasks.fix_missed_scheduledjobs")
def fix_missed_scheduledjobs():
    """
    Fix edgecases where we didnt' ran a job, maybe because of system outage
    Select scheduled jobs which next_run_at is in the past (at least 1 minute older than now)
    Update them with `.update_next()`
    """
    now = datetime.datetime.now(tz=datetime.UTC).replace(second=0, microsecond=0)
    for scheduled_job in ScheduledJob.objects.filter(
        next_run_at__lt=now - datetime.timedelta(minutes=1),
        job__deleted_at__isnull=True,
        job__project__deleted_at__isnull=True,
        job__project__workspace__deleted_at__isnull=True,
    ):
        scheduled_job.update_next()

        celery_app.send_task(
            "job.tasks.send_missed_schedule_notification",
            kwargs={"job_suuid": scheduled_job.job.suuid},
        )


@shared_task(name="job.tasks.launch_scheduled_jobs")
def launch_scheduled_jobs():
    """
    We launch scheduled jobs every minute
    We select jobs for the current minute ()
    We exclude jobs which are scheduled for deletion (or project/workspace)
    """
    now = datetime.datetime.now(tz=datetime.UTC).replace(second=0, microsecond=0)
    for scheduled_job in ScheduledJob.objects.filter(
        next_run_at__gte=now,
        next_run_at__lt=now + datetime.timedelta(minutes=1),
        job__deleted_at__isnull=True,
        job__project__deleted_at__isnull=True,
        job__project__workspace__deleted_at__isnull=True,
    ):
        jobdef = scheduled_job.job
        package = Package.objects.active().filter(project=jobdef.project).order_by("-created_at").first()

        run = Run.objects.create(
            status="PENDING",
            jobdef=jobdef,
            payload_file=None,
            package=package,
            trigger="SCHEDULE",
            created_by_user=scheduled_job.member.user,
        )
        transaction.on_commit(
            lambda run=run: celery_app.send_task(
                "job.tasks.start_run",
                kwargs={"run_suuid": run.suuid},
            )
        )
        scheduled_job.update_last(timestamp=now)
        scheduled_job.update_next()
