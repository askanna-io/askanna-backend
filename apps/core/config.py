import collections
import dataclasses

import yaml
from django.conf import settings
from yaml.scanner import ScannerError

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from core.utils import is_valid_timezone, parse_cron_line
from core.utils.config import get_setting


class AskAnnaConfig:
    """
    Reads the askanna.yml and converts this into usable config object
    """

    notifications: dict = {}

    # Within AskAnna, we have several variables reserved
    reserved_keys = (
        "askanna",
        "cluster",
        "environment",
        "image",
        "job",
        "project",
        "push-target",
        "notifications",
        "timezone",
        "variables",
        "worker",
    )

    def __init__(self, config: dict | None = None, *args, **kwargs):
        self.config = {} if config is None else config
        self.jobs = collections.OrderedDict()
        self.__extract_notifications()
        self.__extract_jobs()

    def __extract_jobs(self):
        jobs = list(set(self.config.keys()) - set(self.reserved_keys))

        # create or find jobdef for each found jobs
        for job in jobs:
            job_in_yaml = self.config.get(job)
            if not isinstance(job_in_yaml, dict):
                # no dict, so not a job definition
                continue
            self.jobs[job] = Job.from_dict(
                name=job,
                job_config=job_in_yaml,
                global_config=self,
            )

    def __extract_notifications(self):
        """
        Just a simple extraction now, no validation yet
        """
        notifications = self.config.get("notifications", {})
        notifications["all"] = notifications.get("all", {"email": []})
        notifications["error"] = notifications.get("error", {"email": []})
        self.notifications = notifications

    @classmethod
    def from_stream(cls, filename):
        try:
            config = yaml.load(filename, Loader=Loader)  # nosec: B506
        except ScannerError:
            return None
        else:
            return cls(config=config)

    @property
    def timezone(self):
        """
        Get the project timezone from the config. If not set or invalid, we take the default timezone from
        django.conf.settings.
        """
        timezone = self.config.get("timezone", "")
        return timezone if is_valid_timezone(timezone) else settings.TIME_ZONE

    @property
    def environment(self):
        """
        Return the environment that is set or the default environment
        """
        environment = self.config.get("environment", {})
        if not environment or not isinstance(environment, dict):
            """
            When the environment is not defined or not a dictionary, we will return the default values configured.
            """
            default_runner_image = get_setting(name="RUNNER_DEFAULT_DOCKER_IMAGE")
            default_runner_image_username = get_setting(name="RUNNER_DEFAULT_DOCKER_IMAGE_USERNAME")
            default_runner_image_password = get_setting(name="RUNNER_DEFAULT_DOCKER_IMAGE_PASSWORD")

            image_spec: dict[str, str | dict] = {"image": default_runner_image}
            if default_runner_image_username:
                image_spec["credentials"] = {
                    "username": default_runner_image_username,
                    "password": default_runner_image_password,
                }

            return Environment.from_dict(image_spec)

        return Environment.from_dict(
            {
                "image": environment.get("image"),
                "credentials": {
                    "username": environment.get("credentials", {}).get("username"),
                    "password": environment.get("credentials", {}).get("password"),
                },
            }
        )


@dataclasses.dataclass
class Schedule:
    raw_definition: str | dict
    cron_definition: str
    cron_timezone: str

    @classmethod
    def from_python(cls, schedule: str | dict, job_timezone):
        try:
            cron_line_parsed = parse_cron_line(schedule)
        except ValueError:
            # FIXME: in the future we should provide feedback to the user that the proposed Schedule is not valid
            return None
        else:
            return cls(
                raw_definition=schedule,
                cron_definition=cron_line_parsed,
                cron_timezone=job_timezone,
            )


@dataclasses.dataclass
class ImageCredentials:
    username: str
    password: str | None = None


@dataclasses.dataclass
class Environment:
    image: str
    credentials: ImageCredentials | None = None

    def has_credentials(self) -> bool:
        """
        Helper function to tell the outside world whether we have credentials set for the environment
        """
        return self.credentials is not None

    def to_dict(self):
        spec: dict[str, str | dict] = {"image": self.image}
        if self.credentials is not None:
            spec["credentials"] = {
                "username": self.credentials.username,
                "password": self.credentials.password,
            }
        return spec

    @classmethod
    def from_dict(cls, environment: dict):
        spec: dict[str, str | dict] = {"image": environment.get("image", "")}
        if environment.get("credentials") and environment.get("credentials", {}).get("username"):
            # Credentials are specified, we just assume at least the username is filled out.
            credentials = ImageCredentials(
                **{
                    "username": environment.get("credentials", {}).get("username", ""),
                    "password": environment.get("credentials", {}).get("password", None),
                }
            )
            spec["credentials"] = credentials

        return cls(**spec)


@dataclasses.dataclass
class Job:
    name: str
    environment: Environment
    commands: list[str]
    notifications: dict
    schedules: list[Schedule]
    timezone: str

    def __flatten_email_receivers(self, receivers: list) -> list:
        _receivers = []
        for r in receivers:
            receiver = r.split(",")
            _receivers += receiver

        return list(set(_receivers))

    def get_notifications(self, medium: str = "email", levels: list | None = None) -> list:
        levels = ["all"] if levels is None else levels.copy()

        # get global
        receivers = []

        # get warning level if set
        for level in levels:
            receivers += self.__flatten_email_receivers(self.notifications.get(level, {}).get(medium, []))

        return list(set(receivers))

    @classmethod
    def from_dict(cls, name, job_config, global_config: AskAnnaConfig):
        global_timezone = global_config.timezone
        global_environment = global_config.environment

        job_config_timezone = job_config.get("timezone", "")
        job_timezone = job_config_timezone if is_valid_timezone(job_config_timezone) else global_timezone

        schedules = []
        for schedule in job_config.get("schedule", []):
            s = Schedule.from_python(schedule, job_timezone)
            # we only add the schedule if it is valid
            if isinstance(s, Schedule):
                schedules.append(s)

        # extract the environment
        job_environment = job_config.get("environment", global_environment.to_dict())
        environment = Environment.from_dict(job_environment)

        # extract the commands
        job_commands = job_config.get("job", [])

        # extract the notifications
        job_notifications: dict = job_config.get("notifications", {})

        # update the job notifications with those in `global_config.notifications`
        # FIXME: make merging of these list pretier
        # update global
        job_notifications["all"] = {"email": job_config.get("notifications", {}).get("all", {}).get("email", [])}
        job_notifications["all"]["email"] += global_config.notifications.get("all", {}).get("email", [])
        job_notifications["all"]["email"] = sorted(list(set(job_notifications["all"]["email"])))

        # update error
        job_notifications["error"] = {"email": job_config.get("notifications", {}).get("error", {}).get("email", [])}
        job_notifications["error"]["email"] += global_config.notifications.get("error", {}).get("email", [])
        job_notifications["error"]["email"] = sorted(list(set(job_notifications["error"]["email"])))

        return cls(
            name=name,
            commands=job_commands,
            environment=environment,
            notifications=job_notifications,
            schedules=schedules,
            timezone=job_timezone,
        )
