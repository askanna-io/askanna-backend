import json
import logging

import docker
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from config import celery_app

from core.config import JobConfig
from core.container import (
    ContainerImageBuilder,
    RegistryAuthenticationError,
    RegistryContainerPullError,
    RegistryImageHelper,
)
from core.utils import parse_string
from job.models import RunImage
from run.models import Run, RunVariable

logger = logging.getLogger(__name__)


def get_job_config(run: Run) -> JobConfig | None:
    if not run.package:
        run.add_to_log("Could not find code package")
        return None

    askanna_config = run.package.get_askanna_config()
    if not askanna_config:
        run.add_to_log("Could not find askanna.yml")
        return None

    job_config: JobConfig = askanna_config.jobs.get(run.job.name)
    if not job_config:
        run.add_to_log(f'Job "{run.job.name}" was not found in the askanna.yml.')
        run.add_to_log(
            "If you renamed or removed the job, please make sure you update the askanna.yml as well.",
        )
        run.add_to_log(
            "When you updated the askanna.yml, check if you pushed the latest code to AskAnna.",
        )
        return None

    return job_config


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


def create_run_variable_object(
    run,
    variable_name: str,
    variable_value,
    variable_type: str,
    variable_is_masked: bool = False,
    variable_labels: list | None = None,
) -> RunVariable:
    variable_labels = [] if variable_labels is None else variable_labels.copy()

    spec = {
        "run": run,
        "created_at": timezone.now(),
        "variable": {
            "name": variable_name,
            "value": variable_value,
            "type": variable_type,
        },
        "is_masked": variable_is_masked,
        "label": variable_labels,
    }

    return RunVariable(**spec)


def get_run_variables(run: Run, job_config: JobConfig) -> dict:
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
    if run.payload_file:
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
                variable_type="string",
                variable_is_masked=True if variable_name == "AA_TOKEN" else False,
                variable_labels=labels,
            )
        )

    project_variables = {}
    for variable in run.project.variables.all():
        project_variables[variable.name] = variable.value

        labels = [{"name": "source", "value": "project", "type": "string"}]
        if variable.is_masked:
            labels.append({"name": "is_masked", "value": None, "type": "tag"})

        variables_to_log.append(
            create_run_variable_object(
                run=run,
                variable_name=variable.name,
                variable_value=variable.get_value(),
                variable_type=get_variable_type(variable.value),
                variable_is_masked=variable.is_masked,
                variable_labels=labels,
            )
        )

    payload_variables = {}
    if run.payload_file:
        with run.payload_file.file.open() as payload_file:
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
                        variable_labels=labels,
                    )
                )

    RunVariable.objects.bulk_create(variables_to_log)
    transaction.on_commit(
        lambda: celery_app.send_task(
            "run.tasks.update_run_variables_file_and_meta",
            kwargs={"run_suuid": run.suuid},
        )
    )

    # Create run variables and ensure that variables are unique
    run_variables = {}
    run_variables.update(**project_variables)
    run_variables.update(**payload_variables)
    run_variables.update(**worker_variables)

    return run_variables


def get_run_image(
    run: Run,
    job_config: JobConfig,
    run_variables: dict,
    docker_client: docker.DockerClient,
    docker_debug_log: bool = False,
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
        logger=lambda x: run.add_to_log(message=x, print_log=docker_debug_log),
    )
    try:
        image_helper.get_image_info()
    except (RegistryAuthenticationError, RegistryContainerPullError):
        return None
    except Exception as exc:
        exception_message = f"Error while getting image information: {exc}"

        run.add_to_log(exception_message, print_log=docker_debug_log)
        run.add_to_log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    run.add_to_log("Preparing run environment", print_log=docker_debug_log)
    run.add_to_log(f"Getting image {job_image}", print_log=docker_debug_log)
    run.add_to_log("Check AskAnna requirements and if not available, try to install them", print_log=docker_debug_log)

    logger.info(f"Get image: {job_image}")
    builder = ContainerImageBuilder(
        client=docker_client,
        image_helper=image_helper,
        image_dockerfile_path=str(settings.APPS_DIR / "job/templates"),
        image_dockerfile="custom_Dockerfile",
        logger=lambda x: run.add_to_log(message=x, print_log=docker_debug_log),
    )
    try:
        run_image = builder.get_image()
    except (RegistryContainerPullError, docker.errors.DockerException, TimeoutError):
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        return run.to_failed()
    except Exception as exc:
        exception_message = f"Error while preparing the run image: {exc}"

        run.add_to_log(exception_message, print_log=docker_debug_log)
        run.add_to_log("An error report has been created and send to the AskAnna admins", print_log=docker_debug_log)
        run.add_to_log("", print_log=docker_debug_log)
        run.add_to_log("Run failed", print_log=docker_debug_log)
        run.to_failed()

        raise Exception(exception_message) from exc

    return run_image
