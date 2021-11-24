# -*- coding: utf-8 -*-
import datetime
import json

from django.conf import settings
import docker

from config.celery_app import app as celery_app
from core.container import (
    ContainerImageBuilder,
    RegistryImageHelper,
    RegistryAuthenticationError,
    RegistryContainerPullError,
)
from core.utils import (
    is_valid_timezone,
    get_setting_from_database,
    parse_string,
)
from job.models import (
    JobRun,
    JobVariable,
    RunImage,
    RunVariableRow,
)


def log_run_variables(variable_name, variable_value, project, job, run, masked, labels=[]):
    """
    Log the variables used for the run
    """
    spec = {
        "project_suuid": project.short_uuid,
        "job_suuid": job.short_uuid,
        "run_suuid": run.short_uuid,
        "created": datetime.datetime.now(tz=datetime.timezone.utc),
        "variable": {
            "name": variable_name,
            "value": variable_value,
            "type": "string",
        },
        "label": labels,
    }
    if masked is not None:
        spec["is_masked"] = masked
    RunVariableRow.objects.create(**spec)


def get_project_variables(project, job, run):
    # Get variables for this project / run
    project_variables = {}
    for pv in JobVariable.objects.filter(project=project):
        project_variables[pv.name] = pv.value

        # log the project defined variables
        labels = [{"name": "source", "value": "project", "type": "string"}]
        is_masked = pv.is_masked
        if is_masked:
            labels.append({"name": "is_masked", "value": None, "type": "tag"})
        log_run_variables(
            pv.name,
            pv.get_value(show_masked=False),
            project,
            job,
            run,
            is_masked,
            labels,
        )
    return project_variables


@celery_app.task(bind=True, name="job.tasks.start_run")
def start_run(self, run_uuid):
    print(f"Received message to start jobrun {run_uuid}")

    # get runner image
    # the default image can be set in core.models.Setting
    default_runner_image = get_setting_from_database(
        name="RUNNER_DEFAULT_DOCKER_IMAGE",
        default=settings.RUNNER_DEFAULT_DOCKER_IMAGE,
    )
    default_runner_image_user = get_setting_from_database(
        name="RUNNER_DEFAULT_DOCKER_IMAGE_USER",
        default=settings.ASKANNA_DOCKER_USER,
    )
    default_runner_image_pass = get_setting_from_database(
        name="RUNNER_DEFAULT_DOCKER_IMAGE_PASS",
        default=settings.ASKANNA_DOCKER_PASS,
    )

    docker_debug_log = get_setting_from_database(
        name="DOCKER_DEBUG_LOG",
        default=False,
    )

    # First save current Celery id to the jobid field
    jr = JobRun.objects.get(pk=run_uuid)
    jr.jobid = self.request.id
    jr.save(update_fields=["jobid"])
    jr.to_pending()

    # What is the jobdef specified?
    jd = jr.jobdef
    pl = jr.payload
    pr = jd.project
    op = jr.output
    tv = jr.runvariables.get()

    package = jr.package
    askanna_config = package.get_askanna_config(
        defaults={
            "RUNNER_DEFAULT_DOCKER_IMAGE": default_runner_image,
            "RUNNER_DEFAULT_DOCKER_IMAGE_USER": default_runner_image_user,
            "RUNNER_DEFAULT_DOCKER_IMAGE_PASS": default_runner_image_pass,
        }
    )
    if not askanna_config:
        op.log("Could not find askanna.yml", print_log=docker_debug_log)
        return jr.to_failed()

    global_timezone = is_valid_timezone(askanna_config.timezone, settings.TIME_ZONE)
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
        return jr.to_failed()

    job_timezone = is_valid_timezone(job_config.timezone, global_timezone)
    jr.set_timezone(job_timezone)

    # log the variables set in this run
    # Get variables for this project / run
    project_variables = get_project_variables(project=pr, job=jd, run=jr)

    # configure hostname for this project docker container
    hostname = pr.short_uuid

    # jr_token is the token of the user who started the run
    jr_token = jr.owner.auth_token.key

    # get runner command (default do echo "askanna-runner for project {}")
    runner_command = [
        "/bin/sh",
        "-c",
        "askanna-run-utils get-run-manifest --output /dev/stdout | sh",
    ]

    worker_variables = {
        "AA_TOKEN": jr_token,
        "AA_REMOTE": settings.ASKANNA_API_URL,
        "AA_RUN_SUUID": jr.short_uuid,
        "AA_JOB_NAME": jd.name,
        "AA_PROJECT_SUUID": str(pr.short_uuid),
        "AA_PACKAGE_SUUID": str(package.short_uuid),
        "TZ": job_timezone,
        "LC_ALL": "C.UTF-8",
        "LANG": "C.UTF-8",
    }
    if pl:
        # we have a payload, so set the payload
        worker_variables.update(
            **{
                "AA_PAYLOAD_SUUID": str(pl.short_uuid),
                "AA_PAYLOAD_PATH": "/input/payload.json",
            }
        )

    for variable, value in worker_variables.items():
        # log the worker variables
        labels = [{"name": "source", "value": "worker", "type": "string"}]
        log_run_variables(variable, value, pr, jd, jr, masked=None, labels=labels)

    payload_variables = {}
    if pl and isinstance(pl.payload, dict):
        # we have a valid dict from the payload
        for k, v in pl.payload.items():
            if isinstance(v, (list, dict)):
                # limit to 10.000 chars
                payload_variables[k] = json.dumps(v)[:10000]
            elif isinstance(v, (str)):
                # limit to 10.000 chars
                payload_variables[k] = v[:10000]
            else:
                # we have a bool or number
                payload_variables[k] = v

    for variable, value in payload_variables.items():
        # log the payload variables
        labels = [{"name": "source", "value": "payload", "type": "string"}]
        log_run_variables(variable, value, pr, jd, jr, masked=None, labels=labels)

    # update the meta of trackedvariables
    tv.update_meta()

    # set environment variables
    env_variables = {}
    env_variables.update(**project_variables)
    env_variables.update(**payload_variables)
    env_variables.update(**worker_variables)

    # start the run
    jr.to_inprogress()

    # start composing docker
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

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
    imagehelper = RegistryImageHelper(
        client,
        job_image,
        username=job_image_username,
        password=job_image_password,
        logger=lambda x: op.log(message=x, print_log=docker_debug_log),
    )

    try:
        imagehelper.login()
        # get information about the image
        imagehelper.info()
    except (RegistryAuthenticationError, RegistryContainerPullError):
        return jr.to_failed()

    op.log("Preparing run environment", print_log=docker_debug_log)
    op.log(f"Getting image {imagehelper.image_uri}", print_log=docker_debug_log)
    op.log(
        "Check AskAnna requirements and if not available, try to install them",
        print_log=docker_debug_log,
    )

    builder = ContainerImageBuilder(
        client=client,
        logger=lambda x: op.log(message=x, print_log=docker_debug_log),
    )
    try:
        run_image = builder.get_image(
            repository=imagehelper.repository,
            tag=imagehelper.image_tag,
            digest=imagehelper.image_sha,
            imagehelper=imagehelper,
            model=RunImage,
            docker_debug_log=docker_debug_log,
            image_prefix=settings.ASKANNA_ENVIRONMENT,
            image_template_path=str(settings.APPS_DIR.path("job/templates/")),
        )
    except (RegistryContainerPullError, docker.errors.DockerException):
        return jr.to_failed()

    op.log("All AskAnna requirements are available", print_log=docker_debug_log)
    op.log("", print_log=docker_debug_log)  # left blank intentionally

    # register that we are using this run_image
    jr.set_run_image(run_image)

    print("Starting image: ", job_image)
    try:
        container = client.containers.run(
            run_image.cached_image,
            runner_command,
            environment=env_variables,
            name="run_{jobrun_suuid}".format(jobrun_suuid=jr.short_uuid),
            labels={
                "run": jr.short_uuid,
                "project": pr.short_uuid,
                "job": jd.short_uuid,
                "askanna_environment": settings.ASKANNA_ENVIRONMENT,
            },
            hostname=hostname,
            stdout=True,
            stderr=True,
            detach=True,
            auto_remove=False,  # always false, otherwise we are not able to capture logs from very short runs
        )
    except (docker.errors.APIError, docker.errors.DockerException) as e:
        print(e)
        op.log(
            f"Run could not be started because of run errors in the image {job_image}",
            print_log=docker_debug_log,
        )
        op.log(e.explanation, print_log=docker_debug_log)
        op.log(
            "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
            print_log=docker_debug_log,
        )
        return jr.to_failed()

    # celery_app.send_task(
    #     "job.tasks.log_stats_from_container",
    #     args=None,
    #     kwargs={"container_id": container.id, "jobrun_suuid": jr.short_uuid},
    # )

    # logs = container.logs()
    for idx, log in enumerate(container.logs(stream=True, timestamps=True)):
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        op.log(message=logline[2], timestamp=logline[1], print_log=docker_debug_log)

        if logline[-1].startswith("AskAnna exit_code="):
            return jr.to_failed(exit_code=int(logline[-1].replace("AskAnna exit_code=", "")))

        if "askanna-run-utils: command not found" in logline[-1]:
            op.log(
                "We could not find an askanna installation on this image.",
                print_log=docker_debug_log,
            )
            op.log(
                "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
                print_log=docker_debug_log,
            )
            return jr.to_failed()

    jr.to_completed()
