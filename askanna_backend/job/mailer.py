import json
from typing import Optional

import pytz
from account.models import Membership
from core.config import Job as JobConfig
from core.mail import send_email
from core.utils import flatten, is_valid_email, parse_string, pretty_time_delta
from core.utils.config import get_setting_from_database
from django.conf import settings
from job.models import JobDef as Job
from run.models import Run
from variable.models import Variable


def fill_in_mail_variable(string, variables):
    receivers = parse_string(string, variables)
    return sorted(list(set(receivers.split(","))))


def send_run_notification(
    run_status: str,
    job_config: JobConfig,
    run: Optional[Run] = None,
    job: Optional[Job] = None,
    extra_vars: dict = {},
):
    """Send a notification for a run or tasks related to running jobs

    Args:
        run_status (str): status of the run used to determine the notification level
        job_config (JobConfig): job config to determine the notification receivers
        run (Run, optional): run the notification should be send for (if not provided, job must be provided)
        job (Job, optional): job used to fill in the variables (if not provided, run must be provided)
        extra_vars (dict, optional): Extra variables. Defaults to {}.
    """
    assert run or job, "Either run or job must be provided"
    if run and job:
        assert run.jobdef == job, "The job used in the run is not the same as the job provided as argument."
    elif run and not job:
        job = run.jobdef
    assert job, "Job must be set. Either via run or as argument."

    # determine the notification levels
    # info receivers receive all
    # warning receivers receive warning and error
    # errorr receivers receive errors only
    # format: "event type": ["notification group(s) to receive the notifications"]
    notification_receivers_lookup = {
        "info": ["all"],
        "error": ["all", "error"],
    }

    notification_levels = {
        "SUBMITTED": "info",
        "PENDING": "info",
        "IN_PROGRESS": "info",
        "COMPLETED": "info",
        "FAILED": "error",
        "SCHEDULE_MISSED": "error",
    }

    event_type = notification_levels[run_status]
    notification_receivers = job_config.get_notifications(levels=notification_receivers_lookup[event_type])

    # inject external information to fill the variables
    project_variables = Variable.objects.filter(project=job.project)
    vars = {}
    for variable in project_variables:
        vars[variable.name] = variable.value

    if run and run.payload and isinstance(run.payload.payload, dict):
        # we have a valid dict from the payload
        for k, v in run.payload.payload.items():
            if isinstance(v, (list, dict)):
                # limit to 10.000 chars
                vars[k] = json.dumps(v)[:10000]
            elif isinstance(v, (str)):
                # limit to 10.000 chars
                vars[k] = v[:10000]
            else:
                # we have a bool or number
                vars[k] = v

    notification_receivers = flatten(list(map(lambda mail: fill_in_mail_variable(mail, vars), notification_receivers)))

    # send to workspace admins if this is defined
    if "workspace admins" in notification_receivers:
        # append the e-mail addresses of the workspace admins
        admins = Membership.members.admins().filter(object_uuid=job.project.workspace.uuid)
        for member in admins:
            notification_receivers.append(member.user.email)

    if "workspace members" in notification_receivers:
        # append the e-mail addresses of the workspace members
        members = Membership.members.members().filter(object_uuid=job.project.workspace.uuid)
        for member in members:
            notification_receivers.append(member.user.email)

    # deduplicate
    notification_receivers = list(set(map(lambda x: x.strip(), notification_receivers)))

    email_template = {
        "SUBMITTED": "run_queued",
        "PENDING": "run_queued",
        "IN_PROGRESS": "run_running",
        "COMPLETED": "run_finished",
        "FAILED": "run_failed",
        "SCHEDULE_MISSED": "schedule_missed",
    }

    using_template = email_template.get(run_status, "run_update")
    from_email = get_setting_from_database("DEFAULT_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL)

    template_context = {
        "run_status": run_status,
        "job": job,
        "event_type": event_type,
        "ui_url": get_setting_from_database("ASKANNA_UI_URL", settings.ASKANNA_UI_URL),
    }
    template_context.update(**extra_vars)

    trigger_translation = {
        "API": "API",
        "CLI": "CLI",
        "WORKER": "Worker",
        "SCHEDULE": "Schedule",
        "WEBUI": "Web interface",
        "PYTHON-SDK": "Python SDK",
    }

    if run:
        if run.duration:
            duration_humanized = pretty_time_delta(run.duration)
        else:
            duration_humanized = pretty_time_delta(0)  # we don't have a duration yet

        if run.output.stdout:
            log = run.output.stdout[-15:]  # only the last 15 lines
        else:
            log = []

        if run.created:
            run_created = run.created.astimezone(tz=pytz.timezone(job.timezone))
        else:
            run_created = None

        if run.started:
            run_started = run.started.astimezone(tz=pytz.timezone(job.timezone))
        else:
            run_started = None

        if run.finished:
            run_finished = run.finished.astimezone(tz=pytz.timezone(job.timezone))
        else:
            run_finished = None

        trigger = trigger_translation.get(run.trigger, "Unknown")

        template_context.update(
            **{
                "run": run,
                "result": run.get_result(),
                "log": log,
                "duration_humanized": duration_humanized,
                "run_created": run_created,
                "run_started": run_started,
                "run_finished": run_finished,
                "trigger": trigger,
            }
        )

    for email in notification_receivers:
        # first validate the email address
        if not is_valid_email(email):
            # we skip sending e-mail to this invalid e-mail adress
            continue

        try:
            send_email(
                f"emails/notifications/{using_template}_subject.txt",
                f"emails/notifications/{using_template}.txt",
                f"emails/notifications/{using_template}.html",
                from_email=str(from_email),
                to_email=email,
                context=template_context,
            )
        except Exception as e:
            # Something went wrong sending the e-mail
            print(e)
