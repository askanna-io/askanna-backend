import datetime
from django.urls import reverse
import pytz
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef
from job.models import ScheduledJob


class TestJobScheduleAPI(BaseJobTestDef, APITestCase):
    """
    Test schedules in JobDef

    In this test we solely test on whether the schedules are listed in the job definition
    """

    def setUp(self):
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "short_uuid": self.jobdef.short_uuid},
        )

    def add_schedules_to_job(
        self, job=None, definitions=[], current_dt=datetime.datetime.now(tz=pytz.UTC)
    ):
        for definition in definitions:
            scheduled_job = ScheduledJob.objects.create(
                job=job,
                raw_definition=definition.get("raw_definition"),
                cron_definition=definition.get("cron_definition"),
                cron_timezone=definition.get("cron_timezone"),
                member=definition.get("member"),
            )
            scheduled_job.update_next(current_dt=current_dt)

    def test_empty_schedules_in_jobresponse(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        self.add_schedules_to_job(self.jobdef, definitions=[])

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)
        self.assertTrue(response.data.get("schedules") == [])

    def test_some_schedules_in_jobresponse(self):
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        self.add_schedules_to_job(
            self.jobdef,
            definitions=[
                {
                    "raw_definition": "*/10 * * * *",
                    "cron_definition": "*/10 * * * *",
                    "cron_timezone": "Europe/Amsterdam",
                    "member": self.memberA_member,
                },
                {
                    "raw_definition": "@midnight",
                    "cron_definition": "0 0 * * *",
                    "cron_timezone": "Asia/Hong_Kong",
                    "member": self.memberA_member,
                },
            ],
            current_dt=datetime.datetime(
                year=2021,
                month=4,
                day=12,
                hour=18,
                minute=0,
                second=0,
                tzinfo=pytz.UTC,
            ),
        )

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobdef.short_uuid)
        self.assertEqual(len(response.data.get("schedules")), 2)
        self.assertTrue(
            response.data.get("schedules")
            == [
                {
                    "last_run": None,
                    "next_run": datetime.datetime(2021, 4, 12, 18, 10, tzinfo=pytz.UTC),
                    "cron_definition": "*/10 * * * *",
                    "cron_timezone": "Europe/Amsterdam",
                    "raw_definition": "*/10 * * * *",
                },
                {
                    "last_run": None,
                    "next_run": datetime.datetime(2021, 4, 13, 16, 0, tzinfo=pytz.UTC),
                    "cron_definition": "0 0 * * *",
                    "cron_timezone": "Asia/Hong_Kong",
                    "raw_definition": "@midnight",
                },
            ]
        )
