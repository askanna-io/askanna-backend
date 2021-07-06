# -*- coding: utf-8 -*-
from celery import shared_task
from celery.schedules import crontab
import docker

from config.celery_app import app as celery_app

from .maintanance import clean_containers_after_run, clean_dangling_images  # noqa
from .metrics import extract_metrics_labels, move_metrics_to_rows  # noqa
from .run import start_run  # noqa
from .schedules import fix_missed_scheduledjobs, launch_scheduled_jobs  # noqa
from .variables import extract_variables_labels, move_variables_to_rows  # noqa


@shared_task(bind=True, name="job.tasks.log_stats_from_container")
def log_stats_from_container(self, container_id, jobrun_suuid):
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    container = client.containers.get(container_id)

    statslog = []

    for stat in container.stats(stream=True, decode=True):
        statslog.append(stat)
    # write statslog away to stats database


celery_app.conf.beat_schedule = {
    "launch_scheduled_jobs": {
        "task": "job.tasks.launch_scheduled_jobs",
        "schedule": crontab(minute="*"),
        "args": (),
    },
    "fix_missed_scheduledjobs": {
        "task": "job.tasks.fix_missed_scheduledjobs",
        "schedule": crontab(minute="*/5"),
        "args": (),
    },
    "clean_containers_after_run": {
        "task": "job.tasks.clean_containers_after_run",
        "schedule": crontab(minute="*/5"),
        "args": (),
    },
    "clean_dangling_images": {
        "task": "job.tasks.clean_dangling_images",
        "schedule": crontab(hour="*"),
        "args": (),
    },
}
