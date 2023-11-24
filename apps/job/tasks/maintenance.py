import datetime
import logging

import docker
from dateutil import parser
from django.conf import settings

from config.celery_app import app as celery_app

from core.utils.config import get_setting
from core.utils.maintenance import remove_objects
from job.models.jobdef import JobDef

logger = logging.getLogger(__name__)


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
        logger.info(client.volumes.prune())


@celery_app.task(name="job.tasks.clean_containers_after_run")
def clean_containers_after_run():
    """
    We query all containers from Docker
    We check which ones are older than `DOCKER_AUTO_REMOVE_TTL_HOURS`
    Finally clean the container
    """

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    delete_when_older_than = get_setting(name="DOCKER_AUTO_REMOVE_TTL_HOURS", return_type=float, default=1)

    for container in client.containers.list(filters={"status": "exited"}):
        if not container.name.startswith("run_"):
            continue
        state = container.attrs.get("State")
        finished_at = state.get("FinishedAt")
        labels = container.attrs.get("Config", {}).get("Labels", {})
        askanna_environment = labels.get("askanna_environment")
        if settings.ASKANNA_ENVIRONMENT != askanna_environment:
            continue

        if finished_at:
            finished_dt = parser.isoparse(finished_at)
            age = datetime.datetime.now(tz=datetime.UTC) - finished_dt
            if age > datetime.timedelta(hours=delete_when_older_than):
                logger.info("Removing container", container.name)
                logger.info(container.remove(v=True))


@celery_app.task(name="job.tasks.delete_jobs")
def delete_jobs():
    """
    We delete jobs that are marked to delete. We also check whether the Project (and higher in the hierarchy) is not
    scheduled for deletion. This will otherwise conflict with the delete operation of Job.

    We pass on the queryset to get all objects these will be filtered in the function remove_objects which will handle
    the deletion of the objects after checking the deletion delay.
    """
    remove_objects(
        JobDef.objects.filter(
            deleted_at__isnull=False,
            project__deleted_at__isnull=True,
            project__workspace__deleted_at__isnull=True,
        )
    )
