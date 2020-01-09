# -*- coding: utf-8 -*-
import uuid

from django.db import models
from django.contrib.postgres.fields import JSONField
=======

from core.fields import JSONField

# Define a few enums that will represent options in the models.

## Environment Options
ENV_CHOICES = (
    ('python2.7', 'python2.7'),
    ('python3.5', 'python3.5'),
    ('python3.6', 'python3.6'),
    ('python3.7', 'python3.7'),
)

## Status of a job execution
JOB_STATUS = (
    ('SUBMITTED', 'SUBMITTED'),
    ('COMPLETED', 'COMPLETED'),
    ('PENDING', 'PENDING'),
    ('PAUSED', 'PAUSED'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED'),
)



class JobBase(object):
    """
    Implements main interface towards the Job interface/concept

    Sketching out the actions that we wish to support.

    The actions will be operated on the Job instances and we will expand as
    needed.

    This interface aims to provide generic controlling actions that will be
    independent of the job execution system.
    """

    def start(self):
        """
        Start a Job
        """
        pass

    def stop(self):
        """
        Stop a Job
        """
        pass

    def reset(self):
        """
        """
        pass

    def pause(self):
        """
        Pause execution of a Job
        """
        pass

    def kill(self):
        """
        Kill a Job
        """
        pass

    def info(self):
        """
        Query execution info of Job
        """
        pass


class Job(JobBase):
    pass


class JobDef(models.Model):
    """
    Consider this as the job registry storing the identity of the job itself.

    FIXME:
        - the job name cannot be unique, since this would be across our system
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50)
    project = models.CharField(max_length=30, blank=True, null=True)  # TODO: connect to project app
    function = models.CharField(max_length=100, blank=True, null=True,
                                help_text="Function to execute")

    # FIXME: may be replaced by model_utils and TimeStampedModel if required
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    visible = models.BooleanField(default=True)  # FIXME: add rationale and default value

    environment = models.CharField(max_length=20, choices=ENV_CHOICES,
                                   default='python3.5')
    env_variables = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Job Definition'
        verbose_name_plural = 'Job Definitions'

    @property
    def status(self):
        """
        Returns the state of the last JobRun.
        """
        pass


class JobPayload(models.Model):
    """
    Let's assume that we use this to store the payload for a given JobDef.

    Needs to be separare from JobRun, since the same `JobPayload` can be
    used in multiple JobRuns.

    FIXME:
        - check the form and structure of the "payload". We can argue that
          we only need to care of passing a serialized structure to the job.
          The name of this structure is always `payload` and that object
          will need to be deserialized within the job itself if needed.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    payload = JSONField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Job Payload'
        verbose_name_plural = 'Job Payloads'


class JobRun(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    jobdef = models.ForeignKey('job.JobDef', on_delete=models.DO_NOTHING)
    payload = models.ForeignKey('job.JobPayload', on_delete=models.DO_NOTHING)
    output = models.ForeignKey('job.JobOutput', on_delete=models.DO_NOTHING)
    status = models.CharField(max_length=20, choices=JOB_STATUS)

    created = models.DateTimeField(auto_now_add=True)

    # stats
    runtime = models.IntegerField(default=0)  # FIXME: check with job system
    memory = models.IntegerField(default=0)  # FIXME: check with job system

    # FIXME: check time series storage for info on resource usage

    class Meta:
        verbose_name = 'Job Run'
        verbose_name_plural = 'Job Runs'


class JobOutput(models.Model):
    """
    Includes the result and any other output generated by the job.

    FIXME:
        - did not add modified field, since sounds as if the output should be
          acting as read-only, needs review
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    exit_code = models.IntegerField(default=0)
    return_payload = JSONField(blank=True)
    stdout = JSONField(blank=True)

    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Job Output'
        verbose_name_plural = 'Job Outputs'
