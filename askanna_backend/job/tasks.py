# -*- coding: utf-8 -*-
import json
import os
import sys


from celery import shared_task
from django.conf import settings
from django.utils.module_loading import import_string
import docker

from job.models import JobRun, JobVariable, RunMetrics


@shared_task(bind=True)
def start_jobrun(self, jobrun_uuid):
    print(f"Received message to start jobrun {jobrun_uuid}")

    # First save current Celery id to the jobid field
    jr = JobRun.objects.get(pk=jobrun_uuid)
    jr.jobid = self.request.id
    jr.status = "PENDING"
    jr.save(update_fields=["jobid", "status"])

    # What is the jobdef specified?
    jd = jr.jobdef
    pl = jr.payload

    package = jr.package

    # compose the path to the package in the project
    # This points to the blob location where the package is
    package_path = os.path.join(settings.BLOB_ROOT, str(package.uuid))
    # Add this to the python path for this session, to resolve to the package code
    sys.path.insert(0, package_path)

    sys_modules_before = list(sys.modules)

    try:
        print("*" * 30)
        function_name = jd.function
        user_function = import_string(function_name)
        print(user_function(**pl.payload))
        print("*" * 30)
    except Exception as e:
        print(e)

    sys_modules_after = list(sys.modules)
    added_keys = list(set(sys_modules_after) - set(sys_modules_before))

    for k in added_keys:
        sys.modules.pop(k)

    sys.path.remove(package_path)


@shared_task(bind=True)
def start_jobrun_dockerized(self, jobrun_uuid):
    print(f"Received message to start jobrun {jobrun_uuid}")

    # First save current Celery id to the jobid field
    jr = JobRun.objects.get(pk=jobrun_uuid)
    jr.jobid = self.request.id
    jr.status = "PENDING"
    jr.save(update_fields=["jobid", "status"])

    # What is the jobdef specified?
    jd = jr.jobdef
    pl = jr.payload
    pr = jd.project
    op = jr.output

    # FIXME: when versioning is in, point to version in JobRun
    package = jr.package

    # Get variables for this project / run
    _project_variables = JobVariable.objects.filter(project=pr)
    project_variables = {}
    for pv in _project_variables:
        project_variables[pv.name] = pv.value

    # configure hostname for this project docker container
    hostname = pr.short_uuid

    # start composing docker

    # FIXME: allow configuration of the socket and potential replace library to connect to kubernetes
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    # get runner image
    # FIXME: allow user to define which one to use
    runner_image = "gitlab.askanna.io:4567/askanna/askanna-cli:3.7-slim-master"

    # pull image first
    client.images.pull(
        runner_image,
        auth_config={
            "username": settings.ASKANNA_DOCKER_USER,
            "password": settings.ASKANNA_DOCKER_PASS,
        },
    )

    # jr_token is the token of the user who started the run
    jr_token = jr.owner.auth_token.key

    aa_remote = "{base_url}/v1/".format(base_url=settings.ASKANNA_API_URL)

    # get runner command (default do echo "askanna-runner for project {}")
    runner_command = [
        "/bin/bash",
        "-c",
        "askanna jobrun-manifest --output /dev/stdout | bash",
    ]

    runner_variables = {
        "AA_TOKEN": jr_token,
        "AA_REMOTE": aa_remote,
        "JOBRUN_UUID": str(jr.uuid),
        "JOBRUN_SUUID": jr.short_uuid,
        "JOBRUN_JOBNAME": jd.name,
        "PROJECT_UUID": str(pr.uuid),
        "PROJECT_SUUID": str(pr.short_uuid),
        "PACKAGE_UUID": str(package.uuid),
        "PACKAGE_SUUID": str(package.short_uuid),
        "PAYLOAD_UUID": str(pl.uuid),
        "PAYLOAD_SUUID": str(pl.short_uuid),
        "PAYLOAD_PATH": "/input/payload.json",
        "RESULT_UUID": str(op.uuid),
        "RESULT_SUUID": str(op.short_uuid),
    }

    payload_variables = {}
    if isinstance(pl.payload, dict):
        # we have a valid dict from the payload
        for k, v in pl.payload.items():
            if isinstance(v, (list, dict)):
                # limit to 10.000 chars
                payload_variables["PLV_" + k] = json.dumps(v)[:10000]
            elif isinstance(v, (str)):
                # limit to 10.000 chars
                payload_variables["PLV_" + k] = v[:10000]
            else:
                # we have a bool or number
                payload_variables["PLV_" + k] = v

    # set environment variables
    env_variables = {}
    env_variables.update(**project_variables)
    env_variables.update(**payload_variables)
    env_variables.update(**runner_variables)

    jr.status = "IN_PROGRESS"
    jr.save(update_fields=["status"])

    container = client.containers.run(
        runner_image,
        runner_command,
        environment=env_variables,
        name="run_{jobrun_suuid}".format(jobrun_suuid=jr.short_uuid),
        labels={
            "jobrun": jr.short_uuid,
            "project": pr.short_uuid,
            "jobdef": jd.short_uuid,
        },
        hostname=hostname,
        stdout=True,
        stderr=True,
        detach=True,
        auto_remove=settings.DOCKER_AUTO_REMOVE_CONTAINER,
        # remove=True,  # remove container after run
    )

    # logs = container.logs()
    op.stdout = []
    for idx, log in enumerate(container.logs(stream=True, timestamps=True)):
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        print(logline)
        op.stdout.append(logline)

        if logline[-1].startswith("AskAnna exit_code="):
            # we handle this and set the jr.status = "FAILED"
            op.exit_code = int(logline[-1].replace("AskAnna exit_code=", ""))
            op.save()
            jr.status = "FAILED"
            jr.save()
            return

    op.save()

    jr.status = "COMPLETED"
    jr.save()


@shared_task(bind=True, name="job.tasks.extract_metrics_labels")
def extract_metrics_labels(self, metrics_uuid):
    """
    Extract labels in .metrics and store the list of labels in .jobrun.labels
    """
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)
    if not runmetrics.metrics:
        # we don't have metrics stored, as this is None (by default on creation)
        return

    alllabels = []
    for metric in runmetrics.metrics:
        labels = metric.get("label")
        if not labels:
            continue

        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

    runmetrics.jobrun.metric_labels = list(set(alllabels) - set([None]))
    runmetrics.jobrun.save(update_fields=["metric_labels"])
