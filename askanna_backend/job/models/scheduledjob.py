import datetime
import zoneinfo

import croniter
from core.models import BaseModel
from django.db import models


class ScheduledJob(BaseModel):
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

    member = models.ForeignKey("account.Membership", on_delete=models.CASCADE, null=True)

    last_run_at = models.DateTimeField(null=True, help_text="The last run of this scheduled job")
    next_run_at = models.DateTimeField(
        null=True,
        help_text="We store the datetime with timzone in UTC of the next run to be queried on",
    )

    def update_last(self, timestamp=datetime.datetime.now(tz=datetime.timezone.utc)):
        self.last_run_at = timestamp
        self.save(
            update_fields=[
                "last_run_at",
                "modified_at",
            ]
        )

    def update_next(self, current_dt=None):
        timezoned_now = current_dt or datetime.datetime.now(tz=datetime.timezone.utc)
        # transform the timezoned_now to target timezone
        timezoned_now = timezoned_now.astimezone(tz=zoneinfo.ZoneInfo(self.cron_timezone))

        it = croniter.croniter(self.cron_definition, timezoned_now)
        next_run_at = it.get_next(ret_type=datetime.datetime)

        self.next_run_at = next_run_at.astimezone(tz=datetime.timezone.utc)
        self.save(
            update_fields=[
                "next_run_at",
                "modified_at",
            ]
        )
