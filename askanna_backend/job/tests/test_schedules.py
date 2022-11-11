import datetime

import pytz
from django.urls import reverse
from job.models import ScheduledJob
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef


class TestJobScheduleAPI(BaseJobTestDef, APITestCase):
    """
    Test schedules in JobDef

    In this test we solely test on whether the schedules are listed in the job definition
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={"version": "v1", "suuid": self.jobdef.suuid},
        )

    def add_schedules_to_job(self, job=None, definitions=[], current_dt=datetime.datetime.now(tz=pytz.UTC)):
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
        self.activate_user("member")

        self.add_schedules_to_job(self.jobdef, definitions=[])

        response = self.client.get(
            self.url,
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("suuid") == self.jobdef.suuid
        assert response.data.get("schedules") is None

    def test_some_schedules_in_jobresponse(self):
        self.activate_user("member")

        self.add_schedules_to_job(
            self.jobdef,
            definitions=[
                {
                    "raw_definition": "*/10 * * * *",
                    "cron_definition": "*/10 * * * *",
                    "cron_timezone": "Europe/Amsterdam",
                    "member": self.members.get("member"),
                },
                {
                    "raw_definition": "@midnight",
                    "cron_definition": "0 0 * * *",
                    "cron_timezone": "Asia/Hong_Kong",
                    "member": self.members.get("member"),
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
        assert response.status_code == status.HTTP_200_OK
        assert response.data.get("suuid") == self.jobdef.suuid
        assert len(response.data.get("schedules")) == 2
        assert response.data.get("schedules") == [
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
