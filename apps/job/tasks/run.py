import logging

import docker
from celery import shared_task
from django.conf import settings

from core.utils.config import get_setting
from job.utils import get_job_config, get_run_image, get_run_variables
from run.models import Run

logger = logging.getLogger(__name__)


@shared_task(name="job.tasks.start_run")
def start_run(run_suuid):
    logger.info(f"Received message to start run {run_suuid}.")
    docker_debug_log = get_setting(name="DOCKER_PRINT_LOG", default=False, return_type=bool)

    run = Run.objects.get(suuid=run_suuid)

    # Prepare run
    run.to_pending()

    job_config = get_job_config(run=run)
    if not job_config:
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    run.set_timezone(job_config.timezone)

    run_variables: dict = get_run_variables(run=run, job_config=job_config)

    # Start the run
    run.to_inprogress()

    docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    run.add_to_log("All AskAnna requirements are available", print_log=docker_debug_log)
    run.add_to_log("", print_log=docker_debug_log)

    run_image = get_run_image(
        run=run,
        job_config=job_config,
        run_variables=run_variables,
        docker_client=docker_client,
        docker_debug_log=docker_debug_log,
    )
    if not run_image:
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    # Register that we are using this run_image
    run.set_run_image(run_image)

    runner_command = [
        "/bin/sh",
        "-c",
        "askanna-run-utils get-run-manifest --output /dev/stdout | sh",
    ]

    logger.info(f"Starting run {run.suuid} with image {run_image}")
    try:
        run_container = docker_client.containers.run(
            image=run_image.cached_image,
            command=runner_command,
            environment=run_variables,
            name=f"aa-run-{run.suuid}",
            labels={
                "run": run.suuid,
                "job": run.job.suuid,
                "project": run.project.suuid,
                "askanna_environment": settings.ASKANNA_ENVIRONMENT,
            },
            privileged=False,
            hostname=run.suuid,
            stdout=True,
            stderr=True,
            detach=True,
            auto_remove=False,  # always false, otherwise we are not able to capture logs from very short runs
            mem_limit="20g",  # memory overall limit for the container
            mem_reservation="20g",  # memory reservation based on actual free memory on the system
            mem_swappiness=0,  # no swap
            memswap_limit="20g",  # Maximum amount of memory + swap a container is allowed to consume.
            cpu_period=10000,  # The length of a CPU period in microseconds.
            cpu_quota=40000,  # Microseconds of CPU time that the container can get in a CPU period.
        )
    except (docker.errors.APIError, docker.errors.DockerException) as exc:
        run.add_to_log(
            f"Run could not be started because of run errors in the image {run_image}",
            print_log=docker_debug_log,
        )
        run.add_to_log(exc.explanation, print_log=docker_debug_log)
        run.add_to_log(
            "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
            print_log=docker_debug_log,
        )
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    logline = []
    for idx, log in enumerate(run_container.logs(stream=True, timestamps=True)):
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        run.add_to_log(message=logline[2], timestamp=logline[1], print_log=docker_debug_log)

        if logline[-1].startswith("AskAnna exit_code="):
            run.add_to_log("", print_log=docker_debug_log)
            run.add_to_log("Run failed", print_log=docker_debug_log)
            return run.to_failed(exit_code=int(logline[-1].replace("AskAnna exit_code=", "")))

        if "askanna-run-utils: command not found" in logline[-1]:
            run.add_to_log(
                "We could not find an askanna installation on this image.",
                print_log=docker_debug_log,
            )
            run.add_to_log(
                "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
                print_log=docker_debug_log,
            )
            run.add_to_log("", print_log=docker_debug_log)
            run.add_to_log("Run failed", print_log=docker_debug_log)
            return run.to_failed()

    if logline[-1] == "Run succeeded":
        return run.to_completed()

    run.add_to_log("", print_log=docker_debug_log)
    run.add_to_log("Run failed", print_log=docker_debug_log)
    return run.to_failed()
