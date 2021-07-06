# -*- coding: utf-8 -*-
import datetime
import json
import os

from config.settings.main import env
from django.db import models
from django.conf import settings

from core.fields import JSONField
from core.models import SlimBaseModel

import redis


class RedisLogQueue:
    def __init__(self, suuid: str):
        self.suuid = suuid
        self.redis_url = env("REDIS_URL")
        self.redis = redis.Redis.from_url(self.redis_url)

    def append(self, log_object: list = None):
        """
        Add log object to queue
        """
        if not log_object:
            return
        return self.redis.rpush(self.suuid, json.dumps(log_object))

    def get(self):
        """
        Return the full queue of logs
        """
        queued_log = self.redis.lrange(self.suuid, 0, -1)
        return list(map(lambda x: json.loads(x), queued_log))

    def remove(self):
        """
        Remove this log queue
        """
        return self.redis.delete(self.suuid)


class JobOutput(SlimBaseModel):
    """
    Includes the result and any other output generated by the job.
    """

    jobdef = models.UUIDField(blank=True, null=True, editable=False)
    jobrun = models.OneToOneField(
        "job.JobRun",
        on_delete=models.CASCADE,
        to_field="uuid",
        related_name="output",
    )
    exit_code = models.IntegerField(default=0)
    stdout = JSONField(blank=True, null=True)
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Storing the mime-type of the output file",
    )
    size = models.PositiveIntegerField(
        editable=False, default=0, help_text="Size of the result stored"
    )
    lines = models.PositiveIntegerField(
        editable=False, default=0, help_text="Number of lines in the result"
    )

    owner = models.CharField(max_length=100, blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logqueue = RedisLogQueue(suuid=self.jobrun.short_uuid)
        self.log_idx = 0

    def log(self, message: str = None, timestamp: str = None, print_log: bool = False):
        self.log_idx += 1
        if not timestamp:
            timestamp = datetime.datetime.utcnow().isoformat()
        self.logqueue.append([self.log_idx, timestamp, message])
        if print_log:
            print([self.log_idx, timestamp, message], flush=True)

    def save_stdout(self):
        self.stdout = self.logqueue.get()
        self.save(update_fields=["stdout"])

        # remove the queue after saving
        self.logqueue.remove()

    def save_exitcode(self, exit_code=0):
        self.exit_code = exit_code
        self.save(update_fields=["exit_code"])

    @property
    def stored_path(self):
        return os.path.join(
            settings.ARTIFACTS_ROOT, self.storage_location, self.filename
        )

    @property
    def storage_location(self):
        return os.path.join(
            self.jobrun.jobdef.project.uuid.hex,
            self.jobrun.jobdef.uuid.hex,
            self.jobrun.uuid.hex,
        )

    @property
    def filename(self):
        return "result_{}.output".format(self.uuid.hex)

    @property
    def read(self):
        """
        Read the result from filesystem and return
        """
        try:
            with open(self.stored_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            return b""

    def prune(self):
        pass
        # not implemented as file yet, the result is stored in the `stdout` field
        # os.remove(self.stored_path)

    class Meta:
        ordering = ["-created"]
        verbose_name = "Job Output"
        verbose_name_plural = "Job Outputs"


class ChunkedJobOutputPart(SlimBaseModel):
    filename = models.CharField(max_length=500)
    size = models.IntegerField(help_text="Size of this resultchunk")
    file_no = models.IntegerField()
    is_last = models.BooleanField(default=False)

    joboutput = models.ForeignKey(
        "job.JobOutput", on_delete=models.CASCADE, blank=True, null=True
    )

    class Meta:
        ordering = ["-created"]
