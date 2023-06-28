import datetime

import pytest
from django.test import TestCase

from job.models import ScheduledJob

pytestmark = pytest.mark.django_db


class TestScheduledJobModel(TestCase):
    def test_model_update_last(self):
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

    def test_model_setnext(self):
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
