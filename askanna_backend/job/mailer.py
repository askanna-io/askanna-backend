# -*- coding: utf-8 -*-
import json

from django.conf import settings
import pytz

from core.config import Job
from core.mail import send_email
from core.utils import (
    flatten,
    is_valid_email,
    get_setting_from_database,
    pretty_time_delta,
    parse_string
)
from job.models import JobRun, JobVariable
from users.models import Membership


def fill_in_mail_variable(string, variables):
    receivers = parse_string(string, variables)
    return sorted(list(set(receivers.split(","))))


def send_run_notification(
    run_status: str,
    run: JobRun = None,
    job: Job = None,
    extra_vars={},
):
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

    event_type = notification_levels.get(run_status)
    notification_receivers = job.get_notifications(
        levels=notification_receivers_lookup.get(event_type)
    )

    vars = {}
    if run:
        # inject external information to fill the variables
        jobvariables = JobVariable.objects.filter(project=run.jobdef.project)
        for variable in jobvariables:
            vars[variable.name] = variable.value

        if run.payload and isinstance(run.payload.payload, dict):
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
        # end of information injection

    notification_receivers = flatten(
        list(
            map(lambda mail: fill_in_mail_variable(mail, vars), notification_receivers)
        )
    )

    # send to workspace admins if this is defined
    if "workspace admins" in notification_receivers:
        # append the e-mail addresses of the workspace admins
        workspace = run.jobdef.project.workspace
        admins = Membership.members.admins().filter(object_uuid=workspace.uuid)
        for member in admins:
            notification_receivers.append(member.user.email)

    if "workspace members" in notification_receivers:
        # append the e-mail addresses of the workspace members
        workspace = run.jobdef.project.workspace
        members = Membership.members.members().filter(object_uuid=workspace.uuid)
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
    from_email = get_setting_from_database(
        "DEFAULT_FROM_EMAIL", settings.DEFAULT_FROM_EMAIL
    )

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

        trigger = trigger_translation.get(run.trigger, "unknown")

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
                from_email=from_email,
                to_email=email,
                context=template_context,
            )
        except Exception as e:
            # Something went wrong sending the e-mail
            print(e)
