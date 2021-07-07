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
from core.utils import is_valid_timezone, get_setting_from_database
from job.models import (
    JobRun,
    JobVariable,
    RunImage,
    RunVariableRow,
)


@celery_app.task(bind=True, name="job.tasks.start_run")
def start_run(self, run_uuid):
    print(f"Received message to start jobrun {run_uuid}")

    # get runner image
    # the default image can be set in core.models.Setting
    runner_image = get_setting_from_database(
        name="RUNNER_DEFAULT_DOCKER_IMAGE",
        default=settings.RUNNER_DEFAULT_DOCKER_IMAGE,
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
    # read unparsed askanna config to get the timezone settings
    askanna_config = package.get_askanna_config()
    if not askanna_config:
        op.log("Could not find askanna.yml", print_log=docker_debug_log)
        return jr.to_failed()

    global_timezone = is_valid_timezone(
        askanna_config.get("timezone"), settings.TIME_ZONE
    )
    job_config = askanna_config.get(jd.name)
    if not job_config:
        op.log(
            f"Job `{jd.name}` was not found in askanna.yml:", print_log=docker_debug_log
        )
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

    job_timezone = is_valid_timezone(job_config.get("timezone"), global_timezone)
    jr.set_timezone(job_timezone)

    # log the variables set in this run
    # Get variables for this project / run
    _project_variables = JobVariable.objects.filter(project=pr)
    project_variables = {}
    for pv in _project_variables:
        project_variables[pv.name] = pv.value

        # log the project defined variables
        labels = [{"name": "source", "value": "project", "type": "string"}]
        is_masked = pv.is_masked
        if is_masked:
            labels.append({"name": "is_masked", "value": None, "type": "tag"})
        RunVariableRow.objects.create(
            **{
                "project_suuid": pr.short_uuid,
                "job_suuid": jd.short_uuid,
                "run_suuid": jr.short_uuid,
                "created": datetime.datetime.now(tz=datetime.timezone.utc),
                "variable": {
                    "name": pv.name,
                    "value": pv.get_value(show_masked=False),
                    "type": "string",
                },
                "is_masked": is_masked,
                "label": labels,
            }
        )

    # configure hostname for this project docker container
    hostname = pr.short_uuid

    # jr_token is the token of the user who started the run
    jr_token = jr.owner.auth_token.key

    aa_remote = "{base_url}/v1/".format(base_url=settings.ASKANNA_API_URL)

    # get runner command (default do echo "askanna-runner for project {}")
    runner_command = [
        "/bin/sh",
        "-c",
        "askanna-run-utils get-run-manifest --output /dev/stdout | sh",
    ]

    worker_variables = {
        "AA_TOKEN": jr_token,
        "AA_REMOTE": aa_remote,
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
        RunVariableRow.objects.create(
            **{
                "project_suuid": pr.short_uuid,
                "job_suuid": jd.short_uuid,
                "run_suuid": jr.short_uuid,
                "created": datetime.datetime.now(tz=datetime.timezone.utc),
                "variable": {
                    "name": variable,
                    "value": value,
                    "type": "string",
                },
                "label": labels,
            }
        )

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
        RunVariableRow.objects.create(
            **{
                "project_suuid": pr.short_uuid,
                "job_suuid": jd.short_uuid,
                "run_suuid": jr.short_uuid,
                "created": datetime.datetime.now(tz=datetime.timezone.utc),
                "variable": {
                    "name": variable,
                    "value": value,
                    "type": "string",
                },
                "label": labels,
            }
        )

    # update the meta of trackedvariables
    tv.update_meta()

    # set environment variables
    env_variables = {}
    env_variables.update(**project_variables)
    env_variables.update(**payload_variables)
    env_variables.update(**worker_variables)

    # read parsed askanna yml to get the environment settings
    askanna_config = package.get_parsed_askanna_config(variables=env_variables)
    if not askanna_config:
        op.log("Could not find askanna.yml", print_log=docker_debug_log)
        return jr.to_failed()

    global_environment = askanna_config.get(
        "environment",
        {
            "image": runner_image,
            "credentials": {
                "username": settings.ASKANNA_DOCKER_USER,
                "password": settings.ASKANNA_DOCKER_PASS,
            },
        },
    )
    job_config = askanna_config.get(jd.name)
    job_environment = job_config.get("environment", global_environment)

    # start the run
    jr.to_inprogress()

    # start composing docker
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    # get image information to determine whether we need to pull this one
    imagehelper = RegistryImageHelper(
        client,
        job_environment.get("image"),
        username=job_environment.get("credentials", {}).get("username"),
        password=job_environment.get("credentials", {}).get("password"),
        logger=lambda x: op.log(message=x, print_log=docker_debug_log),
    )

    try:
        imagehelper.login()
        # get information about the image
        imagehelper.info()
    except (RegistryAuthenticationError, RegistryContainerPullError):
        return jr.to_failed()

    # rule:
    # Can we find the image_short_id in db?
    #   yes: set runner_image to prebuild_image name
    #   no: pull and build

    op.log("Preparing run environment", print_log=docker_debug_log)
    op.log(f"Getting image {imagehelper.image_uri}", print_log=docker_debug_log)
    op.log(
        "Check AskAnna requirements and if not available, try to install them",
        print_log=docker_debug_log,
    )

    run_image, _created = RunImage.objects.get_or_create(
        **{
            "name": imagehelper.repository,
            "tag": imagehelper.image_tag,
            "digest": imagehelper.image_sha,
        }
    )

    if _created or not run_image.cached_image:
        # this is a new image
        # pull image first
        try:
            imagehelper.pull(log=docker_debug_log)
        except RegistryContainerPullError:
            return jr.to_failed()

        # build the new image
        # tag into askanna repo
        repository_name = (
            f"{settings.ASKANNA_ENVIRONMENT}-aa-{run_image.short_uuid}".lower()
        )
        repository_tag = imagehelper.short_id_nosha
        askanna_repository_image_version_name = f"{repository_name}:{repository_tag}"

        builder = ContainerImageBuilder(
            client=client,
        )

        try:
            image, buildlog = builder.build(
                from_image=f"{imagehelper.repository}@{imagehelper.image_sha}",
                tag=askanna_repository_image_version_name,
                template_path=str(settings.APPS_DIR.path("job/templates/")),
                dockerfile="custom_Dockerfile",
            )
        except docker.errors.DockerException as e:
            op.log(
                f"Run could not be started because of run errors in the image {job_environment.get('image')}",
                print_log=docker_debug_log,
            )
            op.log(e.msg, print_log=docker_debug_log)
            op.log(
                "Please follow the instructions on https://docs.askanna.io/ to build your own image.",
                print_log=docker_debug_log,
            )
            return jr.to_failed()

        run_image.cached_image = askanna_repository_image_version_name
        run_image.save(update_fields=["cached_image"])
        # we just created the image with the following short_id:
        print(image.short_id)

        if docker_debug_log:
            # log the build steps into the log, only in DEBUG mode
            map(lambda x: op.log(x.get("stream"), print_log=True), buildlog)

    op.log("All AskAnna requirements are available", print_log=docker_debug_log)
    op.log("", print_log=docker_debug_log)  # left blank intentionally

    # register that we are using this run_image
    jr.set_run_image(run_image)

    print("Starting image: ", job_environment.get("image"))
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
            # always false, otherwise we are not able to capture logs from very short runs
            auto_remove=False,
            # remove=True,  # remove container after run
        )
    except (docker.errors.APIError, docker.errors.DockerException) as e:
        print(e)
        op.log(
            f"Run could not be started because of run errors in the image {job_environment.get('image')}",
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
            return jr.to_failed(
                exit_code=int(logline[-1].replace("AskAnna exit_code=", ""))
            )

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
