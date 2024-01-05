import json
import logging

import docker
from celery import shared_task
from django.conf import settings
from django.utils import timezone

from core.config import Job
from core.container import (
    ContainerImageBuilder,
    RegistryAuthenticationError,
    RegistryContainerPullError,
    RegistryImageHelper,
)
from core.utils import parse_string
from core.utils.config import get_setting
from job.models import RunImage
from run.models import Run, RunVariable

logger = logging.getLogger(__name__)


def create_run_variable_object(
    run,
    variable_name,
    variable_value,
    variable_type: str = "string",
    variable_is_masked: bool = False,
    variable_labels: list | None = None,
) -> RunVariable:
    variable_labels = [] if variable_labels is None else variable_labels.copy()

    spec = {
        "run": run,
        "project_suuid": run.project.suuid,
        "job_suuid": run.job.suuid,
        "run_suuid": run.suuid,
        "created_at": timezone.now(),
        "variable": {
            "name": variable_name,
            "value": variable_value,
            "type": variable_type,
        },
        "label": variable_labels,
    }

    if variable_is_masked is True:
        spec["is_masked"] = variable_is_masked

    return RunVariable(**spec)


def get_variable_type(value) -> str:
    if isinstance(value, dict):
        return "dictionary"
    if isinstance(value, list):
        return "list"
    if isinstance(value, str):
        return "string"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if value is None:
        return "null"

    return "unknown"


def get_run_variables(run: Run, job_config: Job) -> dict:
    # Get and log variables for this run
    variables_to_log = []

    worker_variables = {
        "TZ": job_config.timezone,
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
        "AA_TOKEN": run.created_by_member.user.auth_token.key,
        "AA_REMOTE": settings.ASKANNA_API_URL,
        "AA_RUN_SUUID": run.suuid,
        "AA_JOB_NAME": run.job.name,
        "AA_PACKAGE_SUUID": str(run.package.suuid),
    }
    if run.payload:
        worker_variables.update(
            **{
                "AA_PAYLOAD_PATH": "/input/payload.json",
            }
        )

    for variable_name, variable_value in worker_variables.items():
        # We only log the AskAnna worker variables that start with AA_
        if not variable_name.startswith("AA_"):
            continue

        labels = [{"name": "source", "value": "worker", "type": "string"}]
        variables_to_log.append(
            create_run_variable_object(
                run=run,
                variable_name=variable_name,
                variable_value=variable_value,
                variable_is_masked=True if variable_name == "AA_TOKEN" else False,
                variable_labels=labels,
            )
        )

    project_variables = {}
    for variable in run.project.variables.all():
        project_variables[variable.name] = variable.value

        labels = [{"name": "source", "value": "project", "type": "string"}]
        is_masked = variable.is_masked
        if is_masked:
            labels.append({"name": "is_masked", "value": None, "type": "tag"})

        variables_to_log.append(
            create_run_variable_object(
                run=run,
                variable_name=variable.name,
                variable_value=variable.get_value(),
                variable_type=get_variable_type(variable.value),
                variable_is_masked=is_masked,
                variable_labels=labels,
            )
        )

    payload_variables = {}
    if run.payload:
        with run.payload.file.open() as payload_file:
            payload = json.load(payload_file)

        # If the payload is a dict, we set the keys as environment variables for the run
        if isinstance(payload, dict):
            labels = [{"name": "source", "value": "payload", "type": "string"}]

            for name, value in payload.items():
                variable_type = get_variable_type(value)

                if variable_type in ["dictionary", "list"]:
                    payload_variables[name] = json.dumps(value)[:10000]
                elif variable_type == "string":
                    payload_variables[name] = value[:10000]
                else:
                    payload_variables[name] = value

                variables_to_log.append(
                    create_run_variable_object(
                        run=run,
                        variable_name=name,
                        variable_value=payload_variables[name],
                        variable_type=variable_type,
                        variable_is_masked=None,
                        variable_labels=labels,
                    )
                )

    RunVariable.objects.bulk_create(variables_to_log)
    run.variables_meta.update_meta()

    # Create run variables and ensure that variables are unique
    run_variables = {}
    run_variables.update(**project_variables)
    run_variables.update(**payload_variables)
    run_variables.update(**worker_variables)

    return run_variables


def get_job_config(run: Run, docker_debug_log: bool = False) -> Job | None:
    if not run.package:
        run.output.log("Could not find code package", print_log=docker_debug_log)
        return None

    askanna_config = run.package.get_askanna_config()
    if not askanna_config:
        run.output.log("Could not find askanna.yml", print_log=docker_debug_log)
        return None

    job_config: Job = askanna_config.jobs.get(run.job.name)
    if not job_config:
        run.output.log(f'Job "{run.job.name}" was not found in the askanna.yml.', print_log=docker_debug_log)
        run.output.log(
            "If you renamed or removed the job, please make sure you update the askanna.yml as well.",
            print_log=docker_debug_log,
        )
        run.output.log(
            "When you updated the askanna.yml, check if you pushed the latest code to AskAnna.",
            print_log=docker_debug_log,
        )
        return None

    return job_config


def get_run_image(
    run: Run, job_config: Job, run_variables: dict, docker_client: docker.DockerClient, docker_debug_log: bool = False
) -> RunImage | None:
    # Get image information to determine whether we need to pull this one
    job_image = parse_string(job_config.environment.image, run_variables)
    job_image_username = (
        job_config.environment.has_credentials()
        and parse_string(job_config.environment.credentials.username or "", run_variables)
        or None
    )
    job_image_password = (
        job_config.environment.has_credentials()
        and parse_string(job_config.environment.credentials.password or "", run_variables)
        or None
    )
    image_helper = RegistryImageHelper(
        client=docker_client,
        image_path=job_image,
        username=job_image_username,
        password=job_image_password,
        logger=lambda x: run.output.log(message=x, print_log=docker_debug_log),
    )
    try:
        image_helper.get_image_info()
    except (RegistryAuthenticationError, RegistryContainerPullError):
        return None
    except Exception as exc:
        exception_message = f"Error while getting image information: {exc}"

        run.output.log(exception_message, print_log=docker_debug_log)
        run.output.log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    run.output.log("Preparing run environment", print_log=docker_debug_log)
    run.output.log(f"Getting image {job_image}", print_log=docker_debug_log)
    run.output.log("Check AskAnna requirements and if not available, try to install them", print_log=docker_debug_log)

    logger.info(f"Get image: {job_image}")
    builder = ContainerImageBuilder(
        client=docker_client,
        image_helper=image_helper,
        image_dockerfile_path=str(settings.APPS_DIR / "job/templates"),
        image_dockerfile="custom_Dockerfile",
        logger=lambda x: run.ouptut.log(message=x, print_log=docker_debug_log),
    )
    try:
        run_image = builder.get_image()
    except (RegistryContainerPullError, docker.errors.DockerException, TimeoutError):
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()
    except Exception as exc:
        exception_message = f"Error while preparing the run image: {exc}"

        run.output.log(exception_message, print_log=docker_debug_log)
        run.output.log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    return run_image


@shared_task(name="job.tasks.start_run")
def start_run(run_suuid):
    logger.info(f"Received message to start run {run_suuid}.")
    docker_debug_log = get_setting(name="DOCKER_PRINT_LOG", default=False, return_type=bool)

    run = Run.objects.get(suuid=run_suuid)

    # Prepare run
    run.to_pending()

    job_config = get_job_config(run=run, docker_debug_log=docker_debug_log)
    if not job_config:
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    run.set_timezone(job_config.timezone)

    run_variables: dict = get_run_variables(run=run, job_config=job_config)

    # Start the run
    run.to_inprogress()

    docker_client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    run.output.log("All AskAnna requirements are available", print_log=docker_debug_log)
    run.output.log("", print_log=docker_debug_log)

    run_image = get_run_image(
        run=run,
        job_config=job_config,
        run_variables=run_variables,
        docker_client=docker_client,
        docker_debug_log=docker_debug_log,
    )
    if not run_image:
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
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
        run.output.log(
            f"Run could not be started because of run errors in the image {run_image}",
            print_log=docker_debug_log,
        )
        run.output.log(exc.explanation, print_log=docker_debug_log)
        run.output.log(
            "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
            print_log=docker_debug_log,
        )
        run.output.log("", print_log=docker_debug_log)
        run.output.log("Run failed", print_log=docker_debug_log)
        return run.to_failed()

    logline = []
    for idx, log in enumerate(run_container.logs(stream=True, timestamps=True)):
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        run.output.log(message=logline[2], timestamp=logline[1], print_log=docker_debug_log)

        if logline[-1].startswith("AskAnna exit_code="):
            run.output.log("", print_log=docker_debug_log)
            run.output.log("Run failed", print_log=docker_debug_log)
            return run.to_failed(exit_code=int(logline[-1].replace("AskAnna exit_code=", "")))

        if "askanna-run-utils: command not found" in logline[-1]:
            run.ouput.log(
                "We could not find an askanna installation on this image.",
                print_log=docker_debug_log,
            )
            run.output.log(
                "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
                print_log=docker_debug_log,
            )
            run.output.log("", print_log=docker_debug_log)
            run.output.log("Run failed", print_log=docker_debug_log)
            return run.to_failed()

    if logline[-1] == "Run succeeded":
        return run.to_completed()

    run.output.log("", print_log=docker_debug_log)
    run.ouput.log("Run failed", print_log=docker_debug_log)
    return run.to_failed()
