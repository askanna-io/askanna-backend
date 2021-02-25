# -*- coding: utf-8 -*-
import datetime

from celery.schedules import crontab
from django.conf import settings
from dateutil import parser
import docker

from config.celery_app import app as celery_app


@celery_app.task(name="job.tasks.clean_dangling_images")
def clean_dangling_images():
    """
    We clean dangling images and volumes
    """
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    print(client.images.prune(filters={"dangling": True}))
    print(client.volumes.prune())


@celery_app.task(name="job.tasks.clean_containers_after_run")
def clean_containers_after_run():
    """
    We query all containers from Docker
    We check which ones are older than 72 hours
    Finally clean the container
    """

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    for container in client.containers.list(filters={"status": "exited"}):
        if not container.name.startswith("run_"):
            continue
        state = container.attrs.get("State")
        finished = state.get("FinishedAt")
        labels = container.attrs.get("Config", {}).get("Labels", {})
        askanna_environment = labels.get("askanna_environment")
        if settings.ASKANNA_ENVIRONMENT != askanna_environment:
            continue

        if finished:
            finished_dt = parser.isoparse(finished)
            age = datetime.datetime.now(tz=datetime.timezone.utc) - finished_dt
            if age > datetime.timedelta(hours=72):
                print("Removing container", container.name)
                # remove the container
                # the print makes this removal visible in the logs
                print(container.remove(v=True))


celery_app.conf.beat_schedule = {
    "clean_containers_after_run": {
        "task": "job.tasks.clean_containers_after_run",
        "schedule": crontab(minute="*/5"),
        "args": (),
    },
    "clean_dangling_images": {
        "task": "job.tasks.clean_dangling_images",
        "schedule": crontab(minute="*/15"),
        "args": (),
    },
}
