import datetime
import json
import logging

import redis
from django.db import models

from config.settings.main import env

from core.models import BaseModel

logger = logging.getLogger(__name__)


class RunLog(BaseModel):
    """
    The log generated by a run
    """

    run = models.OneToOneField("run.Run", on_delete=models.CASCADE, related_name="output")
    exit_code = models.IntegerField(default=0)
    stdout = models.JSONField(blank=True, null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logqueue = RedisLogQueue(suuid=self.run.suuid)
        self.log_idx = 0

    def log(self, message: str | None = None, timestamp: str | None = None, print_log: bool = False):
        self.log_idx += 1
        if not timestamp:
            timestamp = datetime.datetime.utcnow().isoformat()
        self.logqueue.append([self.log_idx, timestamp, message])
        if print_log:
            logger.info([self.log_idx, timestamp, message])

    def save_stdout(self):
        self.stdout = self.logqueue.get()
        self.save(
            update_fields=[
                "stdout",
                "modified_at",
            ]
        )

        # remove the queue after saving
        self.logqueue.remove()

    def save_exitcode(self, exit_code=0):
        self.exit_code = exit_code
        self.save(
            update_fields=[
                "exit_code",
                "modified_at",
            ]
        )

    @property
    def lines(self):
        return len(self.stdout) if self.stdout else 0

    @property
    def size(self):
        return len(json.dumps(self.stdout).encode("utf-8")) if self.stdout else 0

    class Meta:
        db_table = "run_log"
        ordering = ["-created_at"]


class RedisLogQueue:
    def __init__(self, suuid: str):
        self.suuid = suuid
        self.redis_url = env("REDIS_URL")
        self.redis = redis.Redis.from_url(self.redis_url)

    def append(self, log_object: list | None = None):
        """
        Add log object to queue
        """
        if log_object:
            return self.redis.rpush(self.suuid, json.dumps(log_object))
        return None

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
