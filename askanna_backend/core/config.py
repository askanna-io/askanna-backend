# -*- coding: utf-8 -*-
import collections
import dataclasses
from typing import Dict, List, Optional

from django.conf import settings

import yaml

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

from core.utils import (
    is_valid_timezone,
    parse_cron_line,
)


class AskAnnaConfig:
    """
    Reads the askanna.yml and converts this into usable config object
    """

    notifications: Dict = {}

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

    def __init__(self, config: Dict = {}, defaults: Dict = {}, *args, **kwargs):
        self.config = config
        self.defaults = defaults
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
    def from_stream(cls, filename, defaults: Dict = {}):
        try:
            config = yaml.load(filename, Loader=Loader)
        except yaml.scanner.ScannerError:
            return None
        else:
            return cls(config=config, defaults=defaults)

    @property
    def timezone(self):
        """
        the global timezone can be set
        if not set we take the default set in our settings
        """
        return is_valid_timezone(self.config.get("timezone"), settings.TIME_ZONE)

    @property
    def environment(self):
        """
        Return the environment that is set
        """
        # get runner image
        # the default image can be set in core.models.Setting
        default_runner_image = self.defaults.get(
            "RUNNER_DEFAULT_DOCKER_IMAGE",
        )
        default_runner_image_user = self.defaults.get(
            "RUNNER_DEFAULT_DOCKER_IMAGE_USER",
        )
        default_runner_image_pass = self.defaults.get(
            "RUNNER_DEFAULT_DOCKER_IMAGE_PASS",
        )

        environment = self.config.get("environment", {})
        if not isinstance(environment, dict) or not environment:
            """
            When the environment is not defined or just a string
            we will return the default values configured.
            """
            return {
                "image": default_runner_image,
                "credentials": {
                    "username": default_runner_image_user,
                    "password": default_runner_image_pass,
                },
            }
        return {
            "image": environment.get("image"),
            "credentials": {
                "username": environment.get("credentials", {}).get("username"),
                "password": environment.get("credentials", {}).get("password"),
            },
        }


@dataclasses.dataclass
class Schedule:
    raw_definition: str
    cron_definition: str
    cron_timezone: str

    @classmethod
    def from_python(cls, schedule: Dict, job_timezone):
        parsed = parse_cron_line(schedule)
        if parsed:
            return cls(
                raw_definition=schedule,
                cron_definition=parsed,
                cron_timezone=job_timezone,
            )
        return None


@dataclasses.dataclass
class ImageCredentials:
    username: str
    password: Optional[str] = None


@dataclasses.dataclass
class Environment:
    image: str
    credentials: Optional[ImageCredentials] = None

    @classmethod
    def from_python(cls, environment: Dict = {}):
        spec = {"image": environment.get("image")}
        if environment.get("credentials"):
            # Credentials are specified, we just assume at least the username is filled out.
            credentials = ImageCredentials(
                **{
                    "username": environment.get("credentials", {}).get("username", ""),
                    "password": environment.get("credentials", {}).get("password"),
                }
            )
            spec["credentials"] = credentials
        return cls(**spec)


@dataclasses.dataclass
class Job:
    name: str
    environment: Environment
    commands: List[str]
    notifications: List[Dict]
    schedules: List[Schedule]
    timezone: str

    def __flatten_email_receivers(self, receivers) -> List:
        _receivers = []
        for r in receivers:
            receiver = r.split(",")
            _receivers += receiver

        return list(set(_receivers))

    def get_notifications(self, medium: str = "email", levels: List = ["all"]) -> List:
        # get global
        receivers = []

        # get warning level if set
        for level in levels:
            receivers += self.__flatten_email_receivers(
                self.notifications.get(level, {}).get(medium, [])
            )

        return list(set(receivers))

    @classmethod
    def from_dict(cls, name, job_config, global_config: AskAnnaConfig):
        global_timezone = global_config.timezone
        global_environment = global_config.environment
        job_timezone = is_valid_timezone(job_config.get("timezone"), global_timezone)

        schedules = []
        for schedule in job_config.get("schedule", []):
            s = Schedule.from_python(schedule, job_timezone)
            # we only add the schedule if it is valid
            if isinstance(s, Schedule):
                schedules.append(s)

        # extract the environment
        job_environment = job_config.get("environment", global_environment)
        environment = Environment.from_python(job_environment)

        # extract the commands
        job_commands = job_config.get("job", [])

        # extract the notifications
        job_notifications = job_config.get("notifications", {})

        # update the job notifications with those in `global_config.notifications`
        # FIXME: make merging of these list pretier
        # update global
        job_notifications["all"] = {
            "email": job_config.get("notifications", {}).get("all", {}).get("email", [])
        }
        job_notifications["all"]["email"] += global_config.notifications.get(
            "all", {}
        ).get("email", [])
        job_notifications["all"]["email"] = sorted(
            list(set(job_notifications["all"]["email"]))
        )

        # update error
        job_notifications["error"] = {
            "email": job_config.get("notifications", {})
            .get("error", {})
            .get("email", [])
        }
        job_notifications["error"]["email"] += global_config.notifications.get(
            "error", {}
        ).get("email", [])
        job_notifications["error"]["email"] = sorted(
            list(set(job_notifications["error"]["email"]))
        )

        return cls(
            name=name,
            commands=job_commands,
            environment=environment,
            notifications=job_notifications,
            schedules=schedules,
            timezone=job_timezone,
        )
