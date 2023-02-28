import datetime
import unittest

import pytest
import pytz
from core.utils import parse_cron_line, parse_cron_schedule
from django.test import TestCase
from job.models import ScheduledJob

pytestmark = pytest.mark.django_db


class TestCron(unittest.TestCase):
    def test_parse_cron_schedule(self):
        schedule = [
            "@yearly",
            "@annually",
            "@monthly",
            "@weekly",
            "@daily",
            "@hourly",
            "errorcron",
            {
                "minute": 1,
            },
            {"minute": 1, "hour": "*"},
            {"minute": 1, "hour": "*", "day": 5},
            {"minute": 1, "hour": "*", "day": 5, "month": 11},
            {"minute": 1, "hour": "*", "month": 11, "weekday": 5},
            ["@weekly"],
        ]
        translated_cron = list(parse_cron_schedule(schedule))
        self.assertEqual(len(schedule), len(translated_cron))

    def test_parse_cron_line_str(self):
        cron_line = "* 1 * 2 *"
        self.assertEqual(parse_cron_line(cron_line), cron_line)

    def test_parse_cron_line_dict(self):
        cron_line = {"minute": 1, "hour": "*", "month": 12, "weekday": 5}
        self.assertEqual(parse_cron_line(cron_line), "1 * * 12 5")

        cron_line = {"weekday": 1}
        self.assertEqual(parse_cron_line(cron_line), "0 0 * * 1")

        cron_line = {"hour": "5", "month": 12, "weekday": "1-5"}
        self.assertEqual(parse_cron_line(cron_line), "0 5 * 12 1-5")

        cron_line = {"minute": "*", "day": 5, "month": 8}
        self.assertEqual(parse_cron_line(cron_line), "* 0 5 8 *")

    def test_parse_cron_line_str_error(self):
        cron_line = "* 1 * 13 *"
        self.assertEqual(parse_cron_line(cron_line), None)

        cron_line = "* * * *"
        self.assertEqual(parse_cron_line(cron_line), None)

        cron_line = "1 2 3 4"
        self.assertEqual(parse_cron_line(cron_line), None)

        cron_line = "* * * * * * *"
        self.assertEqual(parse_cron_line(cron_line), None)


class TestScheduledJobModel(TestCase):
    def test_model_update_last(self):
        scheduled_job = ScheduledJob.objects.create(
            **{
                "cron_definition": "*/5 * 1,15 * *",
                "cron_timezone": "Europe/Amsterdam",
                "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=pytz.UTC),
                "next_run_at": datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=pytz.UTC),
            }
        )

        self.assertEqual(
            scheduled_job.last_run_at,
            datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=pytz.UTC),
        )
        scheduled_job.update_last(timestamp=datetime.datetime(2025, 6, 30, 8, 21, 0, tzinfo=pytz.UTC))
        scheduled_job.refresh_from_db()

        self.assertEqual(
            scheduled_job.last_run_at,
            datetime.datetime(2025, 6, 30, 8, 21, 0, tzinfo=pytz.UTC),
        )

    def test_model_setnext(self):
        scheduled_job = ScheduledJob.objects.create(
            **{
                "cron_definition": "*/5 * 1,15 * *",
                "cron_timezone": "Europe/Amsterdam",
                "last_run_at": datetime.datetime(2021, 3, 3, 0, 10, 0, tzinfo=pytz.UTC),
                "next_run_at": datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=pytz.UTC),
            }
        )
        self.assertEqual(
            scheduled_job.next_run_at,
            datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=pytz.UTC),
        )

        scheduled_job.update_next(current_dt=datetime.datetime(2021, 3, 3, 0, 15, 0, tzinfo=pytz.UTC))
        scheduled_job.refresh_from_db()
        self.assertEqual(
            scheduled_job.next_run_at,
            datetime.datetime(2021, 3, 14, 23, 0, 0, tzinfo=pytz.UTC),
        )

        scheduled_job.update_next(current_dt=datetime.datetime(2050, 3, 15, 0, 15, 0, tzinfo=pytz.UTC))
        scheduled_job.refresh_from_db()
        self.assertEqual(
            scheduled_job.next_run_at,
            datetime.datetime(2050, 3, 15, 0, 20, 0, tzinfo=pytz.UTC),
        )
