# -*- coding: utf-8 -*-
import datetime

from dateutil import parser
from django.conf import settings
import docker

from config.celery_app import app as celery_app
from core.utils import get_setting_from_database


@celery_app.task(name="job.tasks.clean_dangling_images")
def clean_dangling_images():
    """
    We clean dangling images and volumes
    """
    if settings.ASKANNA_ENVIRONMENT == "production":
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")
        # disabled image pruning, because we store `aa-project:version` images which will be unused and cleaned
        # in this action. These images will be used eventually, so disable this function temporarely
        # print(client.images.prune(filters={"dangling": True}))
        print(client.volumes.prune())


@celery_app.task(name="job.tasks.clean_containers_after_run")
def clean_containers_after_run():
    """
    We query all containers from Docker
    We check which ones are older than `DOCKER_AUTO_REMOVE_TTL` hours
    Finally clean the container
    """

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    delete_ttl_after_hours = get_setting_from_database(
        name="DOCKER_AUTO_REMOVE_TTL", default=settings.DOCKER_AUTO_REMOVE_TTL
    )
    delete_after_minutes = int(float(delete_ttl_after_hours) * 60)

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
            if age > datetime.timedelta(minutes=delete_after_minutes):
                print("Removing container", container.name)
                # remove the container
                # the print makes this removal visible in the logs
                print(container.remove(v=True))
