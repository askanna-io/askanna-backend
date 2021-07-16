# -*- coding: utf-8 -*-
import datetime

from dateutil import parser
from django.conf import settings
import docker

from config.celery_app import app as celery_app
from core.utils import get_setting_from_database, remove_objects
from job.models.jobdef import JobDef
from job.models.jobrun import JobRun


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


@celery_app.task(name="job.tasks.delete_jobs")
def delete_jobs():
    """
    We delete jobs that are marked for deleted longer than 5 mins ago
    We also check whether the Project (and higher in the hierarchy) is not scheduled for deletion
    This will otherwise conflict with the delete operation of Job
    """
    remove_objects(
        JobDef.objects.filter(
            project__deleted__isnull=True,
            project__workspace__deleted__isnull=True,
        )
    )


@celery_app.task(name="job.tasks.delete_runs")
def delete_runs():
    """
    We delete runs that are marked for deleted longer than 5 mins ago
    We also check for the condition where the `jobdef` (and higher in the hierarchy) is also not deleted
    Otherwise we would conflict the deletion operation
    """
    remove_objects(
        JobRun.objects.filter(
            jobdef__deleted__isnull=True,
            jobdef__project__deleted__isnull=True,
            jobdef__project__workspace__deleted__isnull=True,
        )
    )
