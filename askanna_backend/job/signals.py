import docker
import os
import sys
import stat
import tempfile

from celery import shared_task

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.module_loading import import_string
from django.db.transaction import on_commit
from django.template.loader import render_to_string


from core.utils import get_config
import django.dispatch

artifact_upload_finish = django.dispatch.Signal(providing_args=["postheaders"])

from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobOutput,
    JobVariable
)
from package.models import Package


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

    # FIXME: fix scheme to https
    aa_remote = "https://{fqdn}/v1/".format(fqdn=settings.ASKANNA_API_FQDN)

    # get runner command (default do echo "askanna-runner for project {}")
    runner_command = [
        "/bin/bash",
        "-c",
        "askanna jobrun-manifest --output /dev/stdout | bash"
    ]

    runner_variables = {
        "AA_TOKEN": jr_token,
        "AA_REMOTE": aa_remote,
        "JOBRUN_UUID": str(jr.uuid),
        "JOBRUN_SHORT_UUID": jr.short_uuid,
        "JOBRUN_JOBNAME": jd.name,
        "PROJECT_UUID": str(pr.uuid),
        "PROJECT_SHORT_UUID": str(pr.short_uuid),
        "PACKAGE_UUID": str(package.uuid),
        "PAYLOAD_UUID": str(pl.uuid),
        "RESULT_UUID": str(op.uuid),
        "PAYLOAD_PATH": "/input/payload.json",
    }

    # set environment variables
    env_variables = {"SECRET": 1}
    env_variables.update(**runner_variables)
    env_variables.update(**project_variables)

    jr.status = "IN_PROGRESS"
    jr.save(update_fields=["status"])

    container = client.containers.run(
        runner_image,
        runner_command,
        environment=env_variables,
        hostname=hostname,
        stdout=True,
        stderr=True,
        detach=True,
        auto_remove=True,
        # remove=True,  # remove container after run
    )

    # logs = container.logs()
    op.stdout = []
    for idx, log in enumerate(container.logs(stream=True, timestamps=True)):
        logline = [idx] + log.decode("utf-8").split(sep=" ", maxsplit=1)
        logline[-1] = logline[-1].rstrip()
        print(logline)
        op.stdout.append(logline)
    op.save()

    jr.status = "COMPLETED"
    jr.save()

# @receiver(post_save, sender=JobDef)
# def create_job_payload_for_new_jobdef_signal(sender, instance, created, **kwargs):  # noqa
#     """
#     Create initial JobPayload when we create a JobDef and set it to active.

#     FIXME:
#         - check with the owner approach, if the property name or field changes
#           in relation to the permission system approach, we will have to
#           adjust accordingly.
#     """
#     if created:
#         try:
#             JobPayload.objects.create(jobdef=instance,
#                                       owner=instance.owner)
#         except Exception as exc:
#             # FIXME: need custom exception for more context
#             raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_output_for_new_jobrun_signal(
    sender, instance, created, **kwargs
):  # noqa
    """
    Create a JobOutput everytime a JobRun gets created.

    FIXME:
        - check with the owner approach, if the property name or field changes
          in relation to the permission system approach, we will have to
          adjust accordingly.
    """
    if created:
        try:
            JobOutput.objects.create(
                jobrun=instance, jobdef=instance.jobdef.uuid, owner=instance.owner
            )
        except Exception as exc:
            # FIXME: need custom exception for more context
            raise Exception("CUSTOM job plumbing Exception: {}".format(exc))


@receiver(post_save, sender=JobRun)
def create_job_for_celery(sender, instance, created, **kwargs):  # noqa
    """
    Every time a new record is created, send the new job to celery
    """
    if created:
        # print(instance.uuid, instance.short_uuid)
        # on_commit(lambda: start_jobrun.delay(instance.uuid))
        on_commit(lambda: start_jobrun_dockerized.delay(instance.uuid))
