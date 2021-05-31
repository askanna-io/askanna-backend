# -*- coding: utf-8 -*-
import datetime

import croniter
from django.db import models
import pytz

from core.models import SlimBaseModel


class ScheduledJob(SlimBaseModel):
    job = models.ForeignKey(
        "job.JobDef",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="schedules",
    )

    raw_definition = models.CharField(max_length=128)
    cron_definition = models.CharField(max_length=128)
    cron_timezone = models.CharField(max_length=64)

    member = models.ForeignKey("users.Membership", on_delete=models.CASCADE, null=True)

    last_run = models.DateTimeField(
        null=True, help_text="The last run of this scheduled job"
    )
    next_run = models.DateTimeField(
        null=True,
        help_text="We store the datetime with timzone in UTC of the next run to be queried on",
    )

    def update_last(self, timestamp=datetime.datetime.now(tz=pytz.UTC)):
        self.last_run = timestamp
        self.save(update_fields=["last_run"])

    def update_next(self, current_dt=None):
        timezoned_now = current_dt or datetime.datetime.now(tz=pytz.UTC)
        # transform the timezoned_now to target timezone
        timezoned_now = timezoned_now.astimezone(tz=pytz.timezone(self.cron_timezone))

        it = croniter.croniter(self.cron_definition, timezoned_now)
        next_run = it.get_next(ret_type=datetime.datetime)
        next_run_in_utc = next_run.astimezone(tz=pytz.UTC)

        self.next_run = next_run_in_utc
        self.save(update_fields=["next_run"])