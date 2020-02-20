# -*- coding: utf-8 -*-
import uuid

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.module_loading import import_string

from core.fields import JSONField  # noqa

from job.settings import JOB_BACKENDS  # noqa

# Define a few enums that will represent options in the models.

## Environment Options  # noqa
ENV_CHOICES = (
    ('python2.7', 'python2.7'),
    ('python3.5', 'python3.5'),
    ('python3.6', 'python3.6'),
    ('python3.7', 'python3.7'),
)

## Status of a job execution  # noqa
JOB_STATUS = (
    ('SUBMITTED', 'SUBMITTED'),
    ('COMPLETED', 'COMPLETED'),
    ('PENDING', 'PENDING'),
    ('PAUSED', 'PAUSED'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED'),
    ('SUCCESS', 'SUCCESS'),
)


def get_job(uuid=None):
    """
    Receives a uuid that is representing a JobDef object.

    Once the object is retrieved, then we know what job backend is in use
    for the particular JobDef object, via the `JobDef.backend` property.

    The proper backend is imported and is called with the uuid to instantiate
    the proper interface.

    returns instantiated job interface object.
    """
    if not uuid:
        raise Exception("need to provide uuid for JobDef")

    try:
        jobdef = JobDef.objects.get(uuid=uuid)
    except JobDef.DoesNotExist:
        # FIXME: raise custom proper Exception
        raise Exception(f"get_job: there is no jobdef with {uuid}")

    try:
        backend = import_string(jobdef.backend)
    except (ImportError, ModuleNotFoundError):
        # FIXME: create proper exception
        print("something is wrong with the backend string")
        raise Exception("Backend String error, cannot load, fix it")

    return backend(uuid=uuid)


def get_job_pk(pk=None):
    """
    Temp used to retrieve a job by pk/id
    """

    try:
        jobdef = JobDef.objects.get(pk=pk)
    except JobDef.DoesNotExist:
        # FIXME: raise custom proper Exception
        raise Exception(f"get_job: there is no jobdef with {uuid}")

    try:
        backend = import_string(jobdef.backend)
    except (ImportError, ModuleNotFoundError):
        # FIXME: create proper exception
        print("something is wrong with the backend string")
        raise Exception("Backend String error, cannot load, fix it")

    return backend(uuid=jobdef.uuid)


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


class Job(JobInterface):
    """
    Concept of Job top-level instance, under review.

    We are still looking out to see if a Job instance instatiation is needed,
    or we can just use functions like `get_job()` to retrieve the proper
    Class based on the backed used in the relevant `JobDef` object.
    """
    def __init__(self, *args, **kwargs):
        self.pk = kwargs.get('pk', None)

        self.uuid = kwargs.get('uuid', None)

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


class JobDef(models.Model):
    """
    Consider this as the job registry storing the identity of the job itself.

    FIXME:
        - the job name cannot be unique, since this would be across our system,
          different clients are very likely to use the same name, and this
          should be fine. The uniqueness is based on the uuid.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50)
    project = models.CharField(max_length=30, blank=True, null=True)  # TODO: connect to project app
    function = models.CharField(max_length=100, blank=True, null=True,
                                help_text="Function to execute")
    backend = models.CharField(max_length=100, choices=JOB_BACKENDS,
                               default='job.celerybackend.CeleryJob')

    # FIXME: may be replaced by model_utils and TimeStampedModel if required
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    visible = models.BooleanField(default=True)  # FIXME: add rationale and default value

    environment = models.CharField(max_length=20, choices=ENV_CHOICES,
                                   default='python3.5')

    # FIXME: Should env_variables be in the JobDef, or JobPayload?
    env_variables = models.TextField(blank=True, null=True)

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

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
        - should we create functions here for tinkering with payloads?
          like serialization/deserialization, type checking, etc...
        - set the active flag to reflect on the payload that is set to
          active for the given JobDef.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    jobdef = models.ForeignKey('job.JobDef', on_delete=models.CASCADE,
                               to_field='uuid',
                               related_name='payload')
    payload = JSONField(blank=True, null=True)

    active = models.BooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Job Payload'
        verbose_name_plural = 'Job Payloads'


class JobRun(models.Model):
    """
    FIXME:
        - I don't think we need JobRun to have an active relationship to the
          jobpayload. It can be a reference to it. If we need to retrieve
          the payload, we can do so, via the uuid.
        - JobRun should have a 1:1 relationship, since there doesn't seem to
          be any reason where we should have a JobRun withouth a JobOutput.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    jobdef = models.ForeignKey('job.JobDef', on_delete=models.CASCADE,
                               to_field='uuid')
    payload = models.UUIDField(blank=True, null=True, editable=False)
    jobid = models.CharField(max_length=120, blank=True, null=True)
    status = models.CharField(max_length=20, choices=JOB_STATUS)

    created = models.DateTimeField(auto_now_add=True)

    # stats
    runtime = models.FloatField(default=0)  # FIXME: check with job system
    memory = models.FloatField(default=0)  # FIXME: check with job system

    # FIXME: check time series storage for info on resource usage

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Job Run'
        verbose_name_plural = 'Job Runs'


class JobOutput(models.Model):
    """
    Includes the result and any other output generated by the job.

    FIXME:
        - did not add modified field, since sounds as if the output should be
          acting as read-only, needs review
        - add the jobdef uuid, since it might be used to fetch all ouputs
          for a given jobdef, withouth having to pass through the JobRun
          object.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    jobdef = models.UUIDField(blank=True, null=True, editable=False)
    jobrun = models.OneToOneField('job.JobRun',
                                  on_delete=models.DO_NOTHING,
                                  to_field='uuid',
                                  related_name='output')
    exit_code = models.IntegerField(default=0)
    return_payload = JSONField(blank=True, null=True)
    stdout = JSONField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    # FIXME: see what name to use, since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Job Output'
        verbose_name_plural = 'Job Outputs'
