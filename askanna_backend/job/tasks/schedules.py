# -*- coding: utf-8 -*-
import datetime

from django.db.transaction import on_commit

from config.celery_app import app as celery_app
from job.models import (
    JobRun,
    ScheduledJob,
)
from package.models import Package


@celery_app.task(name="job.tasks.fix_missed_scheduledjobs")
def fix_missed_scheduledjobs():
    """
    Fix edgecases where we didnt' ran a job, maybe because of system outage
    Select scheduled jobs which next_run is in the past (at least 1 minute older than now)
    Update them with `.update_next()`
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        second=0, microsecond=0
    )
    for job in ScheduledJob.objects.filter(
        next_run__lt=now - datetime.timedelta(minutes=1),
        job__deleted__isnull=True,
        job__project__deleted__isnull=True,
        job__project__workspace__deleted__isnull=True,
    ):
        job.update_next()

        on_commit(
            lambda: celery_app.send_task(
                "job.tasks.send_missed_schedule_notification",
                args=None,
                kwargs={"job_uuid": job.job.uuid},
            )
        )


@celery_app.task(name="job.tasks.launch_scheduled_jobs")
def launch_scheduled_jobs():
    """
    We launch scheduled jobs every minute
    We select jobs for the current minute ()
    We exclude jobs which are scheduled for deletion (or project/workspace)
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        second=0, microsecond=0
    )
    for job in ScheduledJob.objects.filter(
        next_run__gte=now,
        next_run__lt=now + datetime.timedelta(minutes=1),
        job__deleted__isnull=True,
        job__project__deleted__isnull=True,
        job__project__workspace__deleted__isnull=True,
    ):
        jobdef = job.job
        package = (
            Package.objects.filter(finished__isnull=False)
            .filter(project=jobdef.project)
            .order_by("-created")
            .first()
        )

        # create new Jobrun and this will automaticly scheduled
        JobRun.objects.create(
            status="PENDING",
            jobdef=jobdef,
            payload=None,
            package=package,
            trigger="SCHEDULE",
            created_by=job.member.user,
        )
        job.update_last(timestamp=now)
        job.update_next()
