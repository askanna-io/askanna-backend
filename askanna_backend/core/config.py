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

from core.utils import is_valid_timezone, parse_cron_line


class AskAnnaConfig:
    """
    Reads the askanna.yml and converts this into usable config object

    """

    # Within AskAnna, we have several variables reserved
    reserved_keys = (
        "askanna",
        "cluster",
        "environment",
        "image",
        "job",
        "project",
        "push-target",
        "timezone",
        "variables",
        "worker",
    )

    def __init__(self, config: Dict = {}, *args, **kwargs):
        self.config = config
        self.jobs = collections.OrderedDict()
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

    @classmethod
    def from_stream(cls, filename):
        try:
            config = yaml.load(filename, Loader=Loader)
        except yaml.scanner.ScannerError:
            return None
        else:
            return cls(config=config)

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
        Return the envrioment that is set
        """
        environment = self.config.get("environment", {})
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
            credentials = ImageCredentials(
                **{
                    "username": environment.get("credentials", {}).get("username"),
                    "password": environment.get("credentials", {}).get("password"),
                }
            )
            spec["credentials"] = credentials
        return cls(**spec)


@dataclasses.dataclass
class Job:
    name: str
    schedules: List[Schedule]
    timezone: str
    environment: Environment

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
        return cls(
            name=name,
            environment=environment,
            schedules=schedules,
            timezone=job_timezone,
        )
