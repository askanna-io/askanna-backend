import datetime

import pytz
from django.urls import reverse
from job.models import ScheduledJob
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef


class TestJobScheduleAPI(BaseJobTestDef, APITestCase):
    """
    Test schedules in JobDef response

    In this test we solely test on whether the schedules are listed in the job definition
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-detail",
            kwargs={
                "version": "v1",
                "suuid": self.jobdef.suuid,
            },
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

    def test_empty_schedules_in_job_response(self):
        self.activate_user("member")

        self.add_schedules_to_job(self.jobdef, definitions=[])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore
        assert response.data["schedules"] is None  # type: ignore

    def test_schedules_in_job_response(self):
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

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["suuid"] == self.jobdef.suuid  # type: ignore
        assert len(response.data["schedules"]) == 2  # type: ignore
        assert response.data.get("schedules") == [  # type: ignore
            {
                "raw_definition": "*/10 * * * *",
                "cron_definition": "*/10 * * * *",
                "cron_timezone": "Europe/Amsterdam",
                "next_run_at": "2021-04-12T18:10:00Z",
                "last_run_at": None,
            },
            {
                "raw_definition": "@midnight",
                "cron_definition": "0 0 * * *",
                "cron_timezone": "Asia/Hong_Kong",
                "next_run_at": "2021-04-13T16:00:00Z",
                "last_run_at": None,
            },
        ]
