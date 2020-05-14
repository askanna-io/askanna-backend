# -*- coding: utf-8 -*-
import json
import os
import uuid

from django.db import models
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.utils.module_loading import import_string

from core.fields import JSONField  # noqa
from core.models import BaseModel, SlimBaseModel

from job.settings import JOB_BACKENDS  # noqa
from job.models import JOB_STATUS

class JobInterface(object):
    """
    Implements main interface towards the Job interface/concept

    Sketching out the actions that we wish to support.

    The actions will be operated on the Job instances and we will expand as
    needed.

    This interface aims to provide generic controlling actions that will be
    independent of the job execution system.
    """

    def _clean_up_after_run(self):
        """
        Placeholder function to perform a cleanup after a run.

        Depending on the job execution system we can use an appropriate
        post run action to perform/comply with a cleanup operation.

        NOTE:
            - related to an AEP on implementing post job policies
        """
        raise NotImplementedError("This method requires implementation")

    def start(self):
        """
        Start a Job
        """
        raise NotImplementedError("This method requires implementation")

    def stop(self):
        """
        Stop a Job
        """
        raise NotImplementedError("This method requires implementation")

    def reset(self):
        """
        Reset a Job
        """
        raise NotImplementedError("This method requires implementation")

    def pause(self):
        """
        Pause execution of a Job
        """
        raise NotImplementedError("This method requires implementation")

    def kill(self):
        """
        Kill a Job
        """
        raise NotImplementedError("This method requires implementation")

    def info(self):
        """
        Query execution info of Job
        """
        raise NotImplementedError("This method requires implementation")

    def result(self):
        """
        Return the result of the last run of a given Job.
        """
        raise NotImplementedError("This method requires implementation")

    def status(self):
        """
        Return the last known status of a run of a given Job.
        """
        raise NotImplementedError("This method requires implementation")

    def runs(self):
        """
        Return the runs associated with a given Job.
        """
        raise NotImplementedError("This method requires implementation")


class Job(JobInterface):
    """
    Concept of Job top-level instance, under review.

    We are still looking out to see if a Job instance instatiation is needed,
    or we can just use functions like `get_job()` to retrieve the proper
    Class based on the backed used in the relevant `JobDef` object.
    """

    def __init__(self, *args, **kwargs):
        self.pk = kwargs.get("pk", None)

        self.uuid = kwargs.get("uuid", None)

        if self.uuid:
            try:
                jobdef = JobDef.objects.get(uuid=self.uuid)
            except JobDef.DoesNotExist:
                # FIXME: Create proper exception
                print("Deal with the error properly")
                raise Exception("No jobdef found here, fix it")

            # backend job class
            try:
                backend = import_string(jobdef.backend)
            except (ImportError, ModuleNotFoundError):
                # FIXME: create proper exception
                print("something is wrong with the backend string")
                raise Exception("Backend String error, cannot load, fix it")

            self.initjob = backend(uuid=self.uuid)


