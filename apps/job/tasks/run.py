import datetime
import json
import logging

import docker
from django.conf import settings

from config.celery_app import app as celery_app

from core.container import (
    ContainerImageBuilder,
    RegistryAuthenticationError,
    RegistryContainerPullError,
    RegistryImageHelper,
)
from core.utils import parse_string
from core.utils.config import get_setting
from run.models import Run, RunVariable
from variable.models import Variable

logger = logging.getLogger(__name__)


def log_run_variables(
    run, variable_name, variable_value, variable_is_masked=None, variable_labels: list | None = None
):
    """
    Log the variables used for the run
    """
    variable_labels = [] if variable_labels is None else variable_labels.copy()

    spec = {
        "run": run,
        "project_suuid": run.jobdef.project.suuid,
        "job_suuid": run.jobdef.suuid,
        "run_suuid": run.suuid,
        "created_at": datetime.datetime.now(tz=datetime.UTC),
        "variable": {
            "name": variable_name,
            "value": variable_value,
            "type": "string",
        },
        "label": variable_labels,
    }
    if variable_is_masked is not None:
        spec["is_masked"] = variable_is_masked
    RunVariable.objects.create(**spec)


def get_project_variables(run):
    # Get variables for this project / run
    project_variables = {}
    for pv in Variable.objects.filter(project=run.jobdef.project):
        project_variables[pv.name] = pv.value

        # log the project defined variables
        labels = [{"name": "source", "value": "project", "type": "string"}]
        is_masked = pv.is_masked
        if is_masked:
            labels.append({"name": "is_masked", "value": None, "type": "tag"})  # type: ignore
        log_run_variables(
            run=run,
            variable_name=pv.name,
            variable_value=pv.get_value(),
            variable_is_masked=is_masked,
            variable_labels=labels,
        )
    return project_variables


@celery_app.task(bind=True, name="job.tasks.start_run")
def start_run(self, run_uuid):
    logger.info(f"Received message to start run {run_uuid}")

    docker_debug_log = get_setting(name="DOCKER_PRINT_LOG", default=False, return_type=bool)

    # First save current Celery Task ID to the celery_task_id field
    run = Run.objects.get(pk=run_uuid)
    run.celery_task_id = self.request.id
    run.save(
        update_fields=[
            "celery_task_id",
            "modified_at",
        ]
    )
    run.to_pending()

    # What is the jobdef specified?
    jd = run.jobdef
    pl = run.payload
    pr = jd.project
    op = run.output  # type: ignore

    package = run.package
    if not package:
        op.log("Could not find code package", print_log=docker_debug_log)
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    askanna_config = package.get_askanna_config()
    if not askanna_config:
        op.log("Could not find askanna.yml", print_log=docker_debug_log)
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    job_config = askanna_config.jobs.get(jd.name)
    if not job_config:
        op.log(f"Job `{jd.name}` was not found in askanna.yml:", print_log=docker_debug_log)
        op.log(
            "  If you renamed or removed the job, please make sure you update the askanna.yml as well.",
            print_log=docker_debug_log,
        )
        op.log(
            "  When you updated the askanna.yml, check if you pushed the latest code to AskAnna.",
            print_log=docker_debug_log,
        )
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    run.set_timezone(job_config.timezone)

    # Get and log variables for this run

    worker_variables = {
        "TZ": job_config.timezone,
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
        "AA_TOKEN": run.created_by_user.auth_token.key,
        "AA_REMOTE": settings.ASKANNA_API_URL,
        "AA_RUN_SUUID": run.suuid,
        "AA_JOB_NAME": jd.name,
        "AA_PROJECT_SUUID": str(pr.suuid),
        "AA_PACKAGE_SUUID": str(package.suuid),
    }
    if pl:
        # we have a payload, so set the payload
        worker_variables.update(
            **{
                "AA_PAYLOAD_SUUID": str(pl.suuid),
                "AA_PAYLOAD_PATH": "/input/payload.json",
            }
        )

    for variable, value in worker_variables.items():
        # log the worker variables
        labels = [{"name": "source", "value": "worker", "type": "string"}]
        log_run_variables(
            run=run,
            variable_name=variable,
            variable_value=value,
            variable_is_masked=None,
            variable_labels=labels,
        )

    project_variables = get_project_variables(run=run)

    payload_variables = {}
    if pl and isinstance(pl.payload, dict):
        # we have a valid dict from the payload
        for k, v in pl.payload.items():
            if isinstance(v, list | dict):
                # limit to 10.000 chars
                payload_variables[k] = json.dumps(v)[:10000]
            elif isinstance(v, str):
                # limit to 10.000 chars
                payload_variables[k] = v[:10000]
            else:
                # we have a bool or number
                payload_variables[k] = v

    for variable, value in payload_variables.items():
        # log the payload variables
        labels = [{"name": "source", "value": "payload", "type": "string"}]
        log_run_variables(
            run=run,
            variable_name=variable,
            variable_value=value,
            variable_is_masked=None,
            variable_labels=labels,
        )

    # update the meta of trackedvariables
    run.variables_meta.get().update_meta()

    # set environment variables
    env_variables = {}
    env_variables.update(**project_variables)
    env_variables.update(**payload_variables)
    env_variables.update(**worker_variables)

    # start the run
    run.to_inprogress()

    docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    # get image information to determine whether we need to pull this one
    job_image = parse_string(job_config.environment.image, env_variables)
    job_image_username = (
        job_config.environment.has_credentials()
        and parse_string(job_config.environment.credentials.username or "", env_variables)
        or None
    )
    job_image_password = (
        job_config.environment.has_credentials()
        and parse_string(job_config.environment.credentials.password or "", env_variables)
        or None
    )
    image_helper = RegistryImageHelper(
        client=docker_client,
        image_path=job_image,
        username=job_image_username,
        password=job_image_password,
        logger=lambda x: op.log(message=x, print_log=docker_debug_log),
    )
    try:
        image_helper.get_image_info()
    except (RegistryAuthenticationError, RegistryContainerPullError):
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()
    except Exception as exc:
        exception_message = f"Error while getting image information: {exc}"

        op.log(exception_message, print_log=docker_debug_log)
        op.log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    op.log("Preparing run environment", print_log=docker_debug_log)
    op.log(f"Getting image {job_image}", print_log=docker_debug_log)
    op.log("Check AskAnna requirements and if not available, try to install them", print_log=docker_debug_log)

    logger.info(f"Get image: {job_image}")
    builder = ContainerImageBuilder(
        client=docker_client,
        image_helper=image_helper,
        image_dockerfile_path=str(settings.APPS_DIR / "job/templates"),
        image_dockerfile="custom_Dockerfile",
        logger=lambda x: op.log(message=x, print_log=docker_debug_log),
    )
    try:
        run_image = builder.get_image()
    except (RegistryContainerPullError, docker.errors.DockerException, TimeoutError):  # type: ignore
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()
    except Exception as exc:
        exception_message = f"Error while preparing the run image: {exc}"

        op.log(exception_message, print_log=docker_debug_log)
        op.log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    op.log("All AskAnna requirements are available", print_log=docker_debug_log)
    op.log("", print_log=docker_debug_log)  # Left blank intentionally

    # Register that we are using this run_image
    run.set_run_image(run_image)

    runner_command = [
        "/bin/sh",
        "-c",
        "askanna-run-utils get-run-manifest --output /dev/stdout | sh",
    ]

    logger.info(f"Starting run {run.suuid} with image {job_image}")
    try:
        container = docker_client.containers.run(
            image=run_image.cached_image,
            command=runner_command,
            environment=env_variables,
            name=f"aa-run-{run.suuid}",
            labels={
                "run": run.suuid,
                "project": pr.suuid,
                "job": jd.suuid,
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
    except (docker.errors.APIError, docker.errors.DockerException) as exc:  # type: ignore
        op.log(
            f"Run could not be started because of run errors in the image {job_image}",
            print_log=docker_debug_log,
        )
        op.log(exc.explanation, print_log=docker_debug_log)
        op.log(
            "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
            print_log=docker_debug_log,
        )
        op.log("", print_log=docker_debug_log)
        op.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    logline = []
    for idx, log in enumerate(container.logs(stream=True, timestamps=True)):  # type: ignore
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        op.log(message=logline[2], timestamp=logline[1], print_log=docker_debug_log)

        if logline[-1].startswith("AskAnna exit_code="):
            op.log("", print_log=docker_debug_log)
            op.log("Run failed", print_log=docker_debug_log)
            return run.to_failed(exit_code=int(logline[-1].replace("AskAnna exit_code=", "")))

        if "askanna-run-utils: command not found" in logline[-1]:
            op.log(
                "We could not find an askanna installation on this image.",
                print_log=docker_debug_log,
            )
            op.log(
                "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
                print_log=docker_debug_log,
            )
            op.log("", print_log=docker_debug_log)
            op.log("Run failed", print_log=docker_debug_log)
            return run.to_failed()

    if logline[-1] == "Run succeeded":
        return run.to_completed()

    op.log("", print_log=docker_debug_log)
    op.log("Run failed", print_log=docker_debug_log)
    return run.to_failed()
