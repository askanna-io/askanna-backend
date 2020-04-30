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

from core.utils import get_config
from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobOutput,
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

    # FIXME: when versioning is in, point to version in JobRun
    package = Package.objects.filter(project=jd.project).last()

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
    package = Package.objects.filter(project=pr).last()

    # compose the path to the package in the project
    # This points to the blob location where the package is
    package_path = os.path.join(settings.BLOB_ROOT, str(package.uuid))
    host_package_path = os.path.join(settings.HOST_BLOB_ROOT, str(package.uuid))

    # configure hostname for this project docker container
    hostname = pr.short_uuid


    # get path to payload
    payload_path = pl.full_storage_location
    host_payload_path = os.path.join(settings.HOST_PAYLOAD_ROOT, pl.storage_location)
    print(host_payload_path)

    # read config from askanna.yml if any
    config_file_path = os.path.join(package_path, "askanna.yml")
    if not os.path.exists(config_file_path):
        print("askanna.yml not found")
        return

    askanna_config = get_config(config_file_path)
    
    print(askanna_config)

    # see whether we are on the right job
    yaml_config = askanna_config.get(jd.name)
    if not yaml_config:
        print(f"{jd.name} is not specified in this askanna.yml, cannot start job")
        return

    job_commands = yaml_config.get('job')
    function_command = yaml_config.get('function')

    # we don't allow both function and job commands to be set
    if job_commands and function_command:
        print("cannot define both job and function")
        return

    if job_commands:
        print(job_commands)

    if function_command:
        print(function_command)
        # prep script to start this function command

    # start composing docker


    # compose the entrypoint.sh for both single line command
    # and multiline command

    # FIXME: allow configuration of the socket and potential replace library to connect to kubernetes
    client = docker.DockerClient(base_url="unix://var/run/docker.sock")
    # create volume to store askanna code
    volume_1 = client.volumes.create(name=f'vol-{jr.short_uuid}', driver='local',
        labels={"project": pr.short_uuid,
        "askanna-vol": "yes"})
    volume_2 = client.volumes.create(name=f'package-{jr.short_uuid}', driver='local',
        labels={"project": pr.short_uuid,
        "askanna-vol": "package"})

    # print(volume_1.attrs)
    # print(volume_2.attrs)

    # create entrypoint
    tmp_dir = os.path.join(settings.TMP_ROOT, jr.short_uuid)
    host_tmp_dir = os.path.join(settings.HOST_TMP_ROOT, jr.short_uuid)
    os.makedirs(tmp_dir)
    entrypoint_file = os.path.join(tmp_dir, 'askanna-entrypoint.sh')
    print(entrypoint_file)

    # FIXME: remember to use jinja2 for templating, this is easier for now
    with open(entrypoint_file, 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("cd /code\n")
        f.write(f"echo 'askanna-runner for project {pr.title} running on {pr.short_uuid}'\n")
        for command in job_commands:
            print_command = command.replace('"', '\"')
            command = command.replace("{{ PAYLOAD_PATH }}", '$ASKANNA_PAYLOAD_PATH')
            f.write(f"echo '{print_command}'\n")
            f.write( command )
            f.write( "\n")

    # # chmod +x on entrypoint file
    st = os.stat(entrypoint_file)
    os.chmod(entrypoint_file, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    # rsync this to the volume_1
    rsync_container = client.containers.run(
        'netroby/alpine-rsync',
        "ash -c 'rsync -avx --progress /from/ /to/'",
        volumes={
            host_tmp_dir: {"bind": "/from", "mode": "ro"},
            volume_1.name: {"bind": "/to", "mode": "rw"},
        },
        stdout=True,
        stderr=True,
        detach=True,
        # auto_remove=True,
        # remove=True,  # remove container after run
    )

    # for log in rsync_container.logs(stream=True, timestamps=True):
    #     print(log)

    # rsync this to the volume_2 (copy of code)
    rsync_container = client.containers.run(
        'netroby/alpine-rsync',
        "ash -c 'rsync -avx --progress /from/ /to/'",
        volumes={
            host_package_path: {"bind": "/from", "mode": "ro"},
            volume_2.name: {"bind": "/to", "mode": "rw"},
        },
        stdout=True,
        stderr=True,
        detach=True,
        # auto_remove=True,
        # remove=True,  # remove container after run
    )

    # for log in rsync_container.logs(stream=True, timestamps=True):
    #     print(log)

    # get runner image
    runner_image = "python:3"
    # get runner command (default do echo "askanna-runner for project {}")
    runner_command = [
        "echo",
        f"askanna-runner for project {pr.title} running on {pr.short_uuid}",
    ]
    # set environment variables
    env_variables = {"SECRET": 1}
    env_variables.update(
        **{
            "ASKANNA_PAYLOAD_PATH": "/input/payload.json",
        }
    )

    container = client.containers.run(
        runner_image,
        runner_command,
        environment=env_variables,
        entrypoint="/askanna/askanna-entrypoint.sh",
        volumes={
            volume_1.name: {"bind": "/askanna", "mode": "ro"},
            volume_2.name: {"bind": "/code", "mode": "rw"},
            host_payload_path: {"bind": "/input", "mode": "ro"},
        },
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
        logline = [idx] + log.decode('utf-8').split(sep=' ', maxsplit=1)
        print(logline)
        op.stdout.append(logline)

    op.save()

    # volume_1.remove()
    # volume_2.remove()


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
