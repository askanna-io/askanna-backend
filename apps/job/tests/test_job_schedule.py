import datetime

import pytest

from job.models import ScheduledJob
from job.tasks.schedules import fix_missed_scheduledjobs, launch_scheduled_jobs
from run.models import Run

pytestmark = pytest.mark.django_db


def test_model_update_last():
    scheduled_job = ScheduledJob.objects.create(
        **{
            "cron_definition": "*/5 * 1,15 * *",
            "cron_timezone": "Europe/Amsterdam",
            "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=datetime.UTC),
            "next_run_at": datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=datetime.UTC),
        }
    )
    assert scheduled_job.last_run_at == datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=datetime.UTC)

    scheduled_job.update_last(timestamp=datetime.datetime(2025, 6, 30, 8, 21, 0, tzinfo=datetime.UTC))
    scheduled_job.refresh_from_db()
    assert scheduled_job.last_run_at == datetime.datetime(2025, 6, 30, 8, 21, 0, tzinfo=datetime.UTC)


def test_model_setnext():
    scheduled_job = ScheduledJob.objects.create(
        **{
            "cron_definition": "*/5 * 1,15 * *",
            "cron_timezone": "Europe/Amsterdam",
            "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=datetime.UTC),
            "next_run_at": datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=datetime.UTC),
        }
    )
    assert scheduled_job.next_run_at == datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=datetime.UTC)

    scheduled_job.update_next(current_dt=datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=datetime.UTC))
    scheduled_job.refresh_from_db()
    assert scheduled_job.next_run_at == datetime.datetime(2021, 3, 14, 23, 0, 0, tzinfo=datetime.UTC)

    scheduled_job.update_next(current_dt=datetime.datetime(2050, 3, 15, 0, 15, 0, tzinfo=datetime.UTC))
    scheduled_job.refresh_from_db()
    assert scheduled_job.next_run_at == datetime.datetime(2050, 3, 15, 0, 20, 0, tzinfo=datetime.UTC)


def test_fix_missed_scheduledjobs(test_jobs):
    datetime_next_run = datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=datetime.UTC)
    now = datetime.datetime.now(tz=datetime.UTC)

    scheduled_job = ScheduledJob.objects.create(
        **{
            "cron_definition": "*/5 * 1,15 * *",
            "cron_timezone": "Europe/Amsterdam",
            "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=datetime.UTC),
            "next_run_at": datetime_next_run,
            "job": test_jobs.get("job_private"),
        }
    )

    assert scheduled_job.next_run_at == datetime_next_run

    fix_missed_scheduledjobs()
    scheduled_job.refresh_from_db()

    assert scheduled_job.next_run_at != datetime_next_run
    assert scheduled_job.next_run_at > now


def test_launch_scheduled_jobs(test_memberships, test_jobs):
    datetime_next_run = datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(seconds=10)

    scheduled_job = ScheduledJob.objects.create(
        **{
            "cron_definition": "*/5 * 1,15 * *",
            "cron_timezone": "Europe/Amsterdam",
            "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=datetime.UTC),
            "next_run_at": datetime_next_run,
            "job": test_jobs.get("job_private"),
            "member": test_memberships.get("workspace_private_admin"),
        }
    )

    assert scheduled_job.next_run_at == datetime_next_run
    assert Run.objects.all().count() == 0

    launch_scheduled_jobs()
    scheduled_job.refresh_from_db()

    assert scheduled_job.next_run_at > datetime_next_run
    assert Run.objects.all().count() == 1
