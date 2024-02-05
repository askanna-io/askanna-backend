import json
import logging
import time
from typing import TYPE_CHECKING

import redis
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone

from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file

if TYPE_CHECKING:
    from run.models import Run

logger = logging.getLogger(__name__)


class RedisRunLogQueue:
    """
    A class to handle the Run Log Queue in Redis. It's also possible to write the queue to a storage file and save the
    reference to the file in the run's log_file field.
    """

    def __init__(self, run: "Run"):
        self.run = run
        self.redis_queue_name = f"run.RunLogQueue:log:{self.run.suuid}"
        self.redis = redis.Redis.from_url(settings.REDIS_URL)
        self.log_idx = self.redis.llen(self.redis_queue_name)

    def add(self, message: str, timestamp: str | None = None, print_log: bool = False) -> None:
        """
        Add log message to the run log queue

        Args:
            message (str): The message to add to the log queue
            timestamp (str): The timestamp of the log message. Defaults to django.utils.timezone.now().isoformat().
            print_log (bool): Whether to print the log message to the console. Defaults to False.
        """
        self.log_idx += 1
        if not timestamp:
            timestamp = timezone.now().isoformat()

        log_object = [self.log_idx, timestamp, message]

        self.redis.rpush(self.redis_queue_name, json.dumps(log_object))

        if print_log:
            logger.info(log_object)

    def get(self) -> list[list | None]:
        """
        Return the full queue of the run log
        """
        queued_log = self.redis.lrange(self.redis_queue_name, 0, -1)
        return list(map(lambda x: json.loads(x), queued_log))

    def write_to_file(self, force: bool = False, force_max_retries: int = 60) -> None:
        """
        Write the run log queue to a file that is attached to the log_file field of the run

        Args:
            force (bool): Whether to force the writing to a file. Defaults to False.
        """
        lock_key = f"run.RunLogQueue:save_log_file:{self.run.suuid}"

        if force is True and cache.get(lock_key) is True:
            retries = 0
            while True:
                if cache.get(lock_key) is not True or retries > force_max_retries:
                    break
                retries += 1
                time.sleep(1)
        else:
            assert cache.get(lock_key) is not True, "RunLogQueue is already writing the log to a file"

        if self.log_idx > 0:
            cache.set(lock_key, True, timeout=60)
            try:
                log_content_file = ContentFile(
                    json.dumps(self.get()).encode(),
                    name="log.json",
                )
                if self.run.log_file:
                    self._update_log_file(log_content_file)
                else:
                    self._create_log_file(log_content_file)

            finally:
                cache.delete(lock_key)

    def _create_log_file(self, log_content_file: ContentFile) -> None:
        """
        Create a new run log file and save it to the run

        Args:
            log_content_file (ContentFile): The content of the log file
        """
        self.run.log_file = File.objects.create(
            name=log_content_file.name,
            file=log_content_file,
            size=log_content_file.size,
            etag=get_md5_from_file(log_content_file),
            content_type=get_content_type_from_file(log_content_file),
            created_for=self.run,
            created_by=self.run.created_by_member,
            completed_at=timezone.now(),
        )

        self.run.save(
            update_fields=[
                "log_file",
                "modified_at",
            ]
        )

    def _update_log_file(self, log_content_file) -> None:
        """
        Update the existing run log file and update the run meta information

        Args:
            log_content_file (ContentFile): The content of the log file
        """
        # Remove old file
        self.run.log_file.file.delete()

        # Update log file
        self.run.log_file.name = log_content_file.name
        self.run.log_file.file = log_content_file
        self.run.log_file.size = log_content_file.size
        self.run.log_file.etag = get_md5_from_file(log_content_file)
        self.run.log_file.content_type = get_content_type_from_file(log_content_file)
        self.run.log_file.completed_at = timezone.now()

        self.run.log_file.save(
            update_fields=[
                "name",
                "file",
                "size",
                "etag",
                "content_type",
                "completed_at",
                "modified_at",
            ]
        )

        self.run.save(
            update_fields=[
                "modified_at",
            ]
        )

    def remove(self) -> None:
        """
        Remove this run's log queue from Redis
        """
        self.redis.delete(self.redis_queue_name)
