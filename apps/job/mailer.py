import json
import logging
import zoneinfo

from account.models.membership import Membership
from core.config import JobConfig
from core.mail import send_email
from core.utils import flatten, is_valid_email, parse_string, pretty_time_delta
from core.utils.config import get_setting
from job.models import JobDef as Job
from run.models import Run
from variable.models import Variable

logger = logging.getLogger(__name__)


def fill_in_mail_variable(string: str, variables: dict) -> list[str]:
    receivers = parse_string(string, variables)
    return sorted(list(set(receivers.split(","))))


def get_job_notification_receivers(receivers: list[str], variables: dict, job: Job) -> list[str]:
    notification_receivers = flatten(
        list(
            map(
                lambda receiver: fill_in_mail_variable(receiver, variables),
                receivers,
            )
        )
    )

    if "workspace admins" in notification_receivers:
        notification_receivers.extend(
            admin.user.email
            for admin in Membership.objects.active_admins().filter(object_uuid=job.project.workspace.uuid)
        )
        notification_receivers.remove("workspace admins")

    if "workspace members" in notification_receivers:
        notification_receivers.extend(
            member.user.email
            for member in Membership.objects.active_members().filter(object_uuid=job.project.workspace.uuid)
        )
        notification_receivers.remove("workspace members")

    # Clean up and deduplicate
    return list(
        set(
            map(
                lambda receiver: receiver.strip(),
                notification_receivers,
            )
        )
    )


def get_notification_variables(job: Job, run: Run | None = None) -> dict:
    variables = {}

    project_variables = Variable.objects.filter(project=job.project)
    for variable in project_variables:
        variables[variable.name] = variable.value

    if run and run.payload_file:
        with run.payload_file.file.open() as payload_file:
            payload = json.load(payload_file)

        if isinstance(payload, dict):
            for key, value in payload.items():
                if isinstance(value, list | dict):
                    # limit to 10.000 chars
                    variables[key] = json.dumps(value)[:10000]
                elif isinstance(value, str):
                    # limit to 10.000 chars
                    variables[key] = value[:10000]
                else:
                    variables[key] = value

    return variables


def send_notification(
    run_status: str,
    job_config: JobConfig,
    run: Run | None = None,
    job: Job | None = None,
    extra_vars: dict | None = None,
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
    extra_vars = {} if extra_vars is None else extra_vars.copy()

    # determine the notification levels
    # info receivers receive all
    # warning receivers receive warning and error
    # error receivers receive errors only
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

    variables = get_notification_variables(job=job, run=run)

    notification_receivers = get_job_notification_receivers(
        job=job,
        receivers=job_config.get_notifications(levels=notification_receivers_lookup[event_type]),
        variables=variables,
    )

    email_template = {
        "SUBMITTED": "run_queued",
        "PENDING": "run_queued",
        "IN_PROGRESS": "run_running",
        "COMPLETED": "run_finished",
        "FAILED": "run_failed",
        "SCHEDULE_MISSED": "schedule_missed",
    }

    using_template = email_template.get(run_status, "run_update")
    from_email = get_setting("DEFAULT_FROM_EMAIL")

    template_context = {
        "run_status": run_status,
        "job": job,
        "event_type": event_type,
        "ui_url": get_setting("ASKANNA_UI_URL"),
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

        if run.created_at:
            run_created_at = run.created_at.astimezone(tz=zoneinfo.ZoneInfo(job.timezone))
        else:
            run_created_at = None

        if run.started_at:
            run_started_at = run.started_at.astimezone(tz=zoneinfo.ZoneInfo(job.timezone))
        else:
            run_started_at = None

        if run.finished_at:
            run_finished_at = run.finished_at.astimezone(tz=zoneinfo.ZoneInfo(job.timezone))
        else:
            run_finished_at = None

        trigger = trigger_translation.get(run.trigger, "Unknown")

        template_context.update(
            **{
                "run": run,
                "result": run.result_file,
                "log": run.get_log()[-15:],  # only the last 15 lines
                "duration_humanized": duration_humanized,
                "run_created_at": run_created_at,
                "run_started_at": run_started_at,
                "run_finished_at": run_finished_at,
                "trigger": trigger,
            }
        )

    for email in notification_receivers:
        if not is_valid_email(email):
            # skip sending e-mail to an invalid e-mail adress, but continue with the rest
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
        except Exception as exc:
            logger.error(f"Something went wrong sending a notification e-mail: {exc}")
