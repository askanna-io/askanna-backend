# -*- coding: utf-8 -*-
import datetime

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
        next_run__lt=now - datetime.timedelta(minutes=1)
    ):
        job.update_next()


@celery_app.task(name="job.tasks.launch_scheduled_jobs")
def launch_scheduled_jobs():
    """
    We launch scheduled jobs every minute
    We select jobs for the current minute ()
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        second=0, microsecond=0
    )
    for job in ScheduledJob.objects.filter(
        next_run__gte=now,
        next_run__lt=now + datetime.timedelta(minutes=1),
    ):
        jobdef = job.job
        package = (
            Package.objects.filter(project=jobdef.project).order_by("-created").first()
        )

        # create new Jobrun and this will automaticly scheduled
        JobRun.objects.create(
            status="PENDING",
            jobdef=jobdef,
            payload=None,
            package=package,
            trigger="SCHEDULE",
            owner=job.member.user,
        )
        job.update_last(timestamp=now)
        job.update_next()
