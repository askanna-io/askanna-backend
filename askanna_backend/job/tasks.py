# -*- coding: utf-8 -*-
import datetime
import json
import os
import sys

from celery import shared_task
from celery.schedules import crontab
from dateutil import parser
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils.module_loading import import_string
import docker

from config.celery_app import app as celery_app
from core.models import Setting
from job.models import (
    JobRun,
    JobVariable,
    RunMetrics,
    RunMetricsRow,
    RunVariableRow,
    RunVariables,
    ScheduledJob,
)

from package.models import Package


@celery_app.task(name="job.tasks.fix_missed_scheduledjobs")
def fix_missed_scheduledjobs():
    """
    Fix edgecases where we didnt' ran a job, maybe because of system outage
    Select scheduled jobs which next_run is in the past
    Update them with `.update_next()`
    """
    for job in ScheduledJob.objects.filter(
        next_run__lt=datetime.datetime.now(tz=datetime.timezone.utc)
    ):
        job.update_next()


@celery_app.task(name="job.tasks.launch_scheduled_jobs")
def launch_scheduled_jobs():
    """
    We launch scheduled jobs every minute
    We select jobs for the current minute ()
    """
    now = datetime.datetime.now(tz=datetime.timezone.utc).replace(
        second=0, microsecond=0
    )
    for job in ScheduledJob.objects.filter(
        next_run__gte=now,
        next_run__lt=now + datetime.timedelta(minutes=1),
    ):
        jobdef = job.job
        package = (
            Package.objects.filter(project=jobdef.project).order_by("-created").first()
        )

        # create new Jobrun and this will automaticly scheduled
        JobRun.objects.create(
            status="PENDING",
            jobdef=jobdef,
            payload=None,
            package=package,
            trigger="SCHEDULE",
            owner=job.member.user,
        )
        job.update_last(timestamp=now)
        job.update_next()


@shared_task(bind=True, name="job.tasks.log_stats_from_container")
def log_stats_from_container(self, container_id, jobrun_suuid):
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    container = client.containers.get(container_id)

    statslog = []

    for stat in container.stats(stream=True, decode=True):
        statslog.append(stat)
    # write statslog away to stats database


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
    jr.save(update_fields=["jobid"])
    jr.to_pending()

    # What is the jobdef specified?
    jd = jr.jobdef
    pl = jr.payload
    pr = jd.project
    op = jr.output
    tv = jr.runvariables.get()

    # FIXME: when versioning is in, point to version in JobRun
    package = jr.package

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

    # start composing docker

    # FIXME: allow configuration of the socket and potential replace library to connect to kubernetes
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

    # get runner image
    # FIXME: allow user to define which one to use
    # the default image can be set in core.models.Setting
    try:
        docker_image_setting = Setting.objects.get(name="RUNNER_DEFAULT_DOCKER_IMAGE")
    except ObjectDoesNotExist:
        runner_image = settings.RUNNER_DEFAULT_DOCKER_IMAGE
    else:
        runner_image = docker_image_setting.value

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
        "askanna-run-utils get-run-manifest --output /dev/stdout | bash",
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
        "RESULT_UUID": str(op.uuid),
        "RESULT_SUUID": str(op.short_uuid),
    }
    if pl:
        # we have a payload, so set the payload
        runner_variables.update(
            **{
                "PAYLOAD_UUID": str(pl.uuid),
                "PAYLOAD_SUUID": str(pl.short_uuid),
                "PAYLOAD_PATH": "/input/payload.json",
            }
        )

    for variable, value in runner_variables.items():
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
                payload_variables["PLV_" + k] = json.dumps(v)[:10000]
            elif isinstance(v, (str)):
                # limit to 10.000 chars
                payload_variables["PLV_" + k] = v[:10000]
            else:
                # we have a bool or number
                payload_variables["PLV_" + k] = v

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
    env_variables.update(**runner_variables)

    jr.to_inprogress()

    container = client.containers.run(
        runner_image,
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
        auto_remove=settings.DOCKER_AUTO_REMOVE_CONTAINER,
        # remove=True,  # remove container after run
    )

    # celery_app.send_task(
    #     "job.tasks.log_stats_from_container",
    #     args=None,
    #     kwargs={"container_id": container.id, "jobrun_suuid": jr.short_uuid},
    # )

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
            op.save(update_fields=["exit_code", "stdout"])
            jr.to_failed()
            return

    op.save(update_fields=["stdout"])
    jr.to_completed()


@shared_task(bind=True, name="job.tasks.extract_metrics_labels")
def extract_metrics_labels(self, metrics_uuid):
    """
    Extract labels in .metrics and store the list of labels in .jobrun.labels
    """
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)
    jobrun = runmetrics.jobrun
    if not runmetrics.metrics:
        # we don't have metrics stored, as this is None (by default on creation)
        return
    alllabels = []
    allkeys = []
    count = 0
    for metric in runmetrics.metrics[::]:
        labels = metric.get("label", [])
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of metrics
        metrics = metric.get("metric", {})
        allkeys.append(metrics.get("name"))
        count += 1

    jobrun.metric_keys = list(set(allkeys) - set([None]))
    jobrun.metric_labels = list(set(alllabels) - set([None]))
    jobrun.save(update_fields=["metric_labels", "metric_keys"])

    runmetrics.count = count
    runmetrics.size = len(json.dumps(runmetrics.metrics))
    runmetrics.save(update_fields=["count", "size"])


@shared_task(bind=True, name="job.tasks.move_metrics_to_rows")
def move_metrics_to_rows(self, metrics_uuid):
    runmetrics = RunMetrics.objects.get(pk=metrics_uuid)

    # remove old rows if any
    RunMetricsRow.objects.filter(run_suuid=runmetrics.short_uuid).delete()

    for metric in runmetrics.metrics:
        metric["created"] = datetime.datetime.fromisoformat(metric["created"])
        metric["project_suuid"] = runmetrics.jobrun.jobdef.project.short_uuid
        metric["job_suuid"] = runmetrics.jobrun.jobdef.short_uuid
        # overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        metric["run_suuid"] = runmetrics.jobrun.short_uuid
        RunMetricsRow.objects.create(**metric)


@shared_task(bind=True, name="job.tasks.extract_variables_labels")
def extract_variables_labels(self, variables_uuid):
    """
    Extract labels in .variables and store the list of labels in .jobrun.labels
    """
    runvariables = RunVariables.objects.get(pk=variables_uuid)
    jobrun = runvariables.jobrun
    if not runvariables.variables:
        # we don't have variables stored, as this is None (by default on creation)
        return
    alllabels = []
    allkeys = []
    count = 0
    for variable in runvariables.variables[::]:
        labels = variable.get("label", [])
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of variable
        variables = variable.get("variable", {})
        allkeys.append(variables.get("name"))
        count += 1

    # also count the ones in the databaase
    dbvariables = RunVariableRow.objects.filter(
        run_suuid=runvariables.short_uuid
    ).exclude(label__contains=[{"name": "source", "value": "run", "type": "string"}])
    for variable in dbvariables:
        labels = variable.label
        for label_obj in labels:
            alllabels.append(label_obj.get("name"))

        # count number of variable
        variables = variable.variable
        allkeys.append(variables.get("name"))
        count += 1

    jobrun.variable_keys = list(set(allkeys) - set([None]))
    jobrun.variable_labels = list(set(alllabels) - set([None]))
    jobrun.save(update_fields=["variable_labels", "variable_keys"])

    runvariables.count = count
    runvariables.size = len(json.dumps(runvariables.variables))
    runvariables.save(update_fields=["count", "size"])


@shared_task(bind=True, name="job.tasks.move_variables_to_rows")
def move_variables_to_rows(self, variables_uuid):
    runvariables = RunVariables.objects.get(pk=variables_uuid)

    # remove old rows with source=run
    RunVariableRow.objects.filter(run_suuid=runvariables.short_uuid).filter(
        label__contains=[{"name": "source", "value": "run", "type": "string"}]
    ).delete()

    for variable in runvariables.variables:
        variable["created"] = datetime.datetime.fromisoformat(variable["created"])
        variable["project_suuid"] = runvariables.jobrun.jobdef.project.short_uuid
        variable["job_suuid"] = runvariables.jobrun.jobdef.short_uuid
        # overwrite run_suuid, even if the run_suuid defined is not right, prevent polution
        variable["run_suuid"] = runvariables.jobrun.short_uuid

        RunVariableRow.objects.create(**variable)


@celery_app.task(name="job.tasks.clean_dangling_images")
def clean_dangling_images():
    """
    We clean dangling images and volumes
    """
    if settings.ASKANNA_ENVIRONMENT == "production":
        client = docker.DockerClient(base_url="unix://var/run/docker.sock")
        print(client.images.prune(filters={"dangling": True}))
        print(client.volumes.prune())


@celery_app.task(name="job.tasks.clean_containers_after_run")
def clean_containers_after_run():
    """
    We query all containers from Docker
    We check which ones are older than 72 hours
    Finally clean the container
    """

    client = docker.DockerClient(base_url="unix://var/run/docker.sock")

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
            if age > datetime.timedelta(hours=72):
                print("Removing container", container.name)
                # remove the container
                # the print makes this removal visible in the logs
                print(container.remove(v=True))


celery_app.conf.beat_schedule = {
    "launch_scheduled_jobs": {
        "task": "job.tasks.launch_scheduled_jobs",
        "schedule": crontab(minute="*"),
        "args": (),
    },
    "fix_missed_scheduledjobs": {
        "task": "job.tasks.fix_missed_scheduledjobs",
        "schedule": crontab(minute="*/5"),
        "args": (),
    },
    "clean_containers_after_run": {
        "task": "job.tasks.clean_containers_after_run",
        "schedule": crontab(minute="*/15"),
        "args": (),
    },
    "clean_dangling_images": {
        "task": "job.tasks.clean_dangling_images",
        "schedule": crontab(hour="*"),
        "args": (),
    },
}
