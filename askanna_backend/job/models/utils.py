
from django.utils.module_loading import import_string

# from job.models import JobDef

# Define a few enums that will represent options in the models.

## Environment Options  # noqa
ENV_CHOICES = (
    ("python2.7", "python2.7"),
    ("python3.5", "python3.5"),
    ("python3.6", "python3.6"),
    ("python3.7", "python3.7"),
)

## Status of a job execution  # noqa
JOB_STATUS = (
    ("SUBMITTED", "SUBMITTED"),
    ("COMPLETED", "COMPLETED"),
    ("PENDING", "PENDING"),
    ("PAUSED", "PAUSED"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("FAILED", "FAILED"),
    ("SUCCESS", "SUCCESS"),
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
        jobdef = JobDef.objects.get(short_uuid=uuid)
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


def get_job_pk(pk=None):
    """
    Temp used to retrieve a job by pk/id
    """

    try:
        jobdef = JobDef.objects.get(pk=pk)
    except JobDef.DoesNotExist:
        # FIXME: raise custom proper Exception
        raise Exception(f"get_job: there is no jobdef with {pk}")

    try:
        backend = import_string(jobdef.backend)
    except (ImportError, ModuleNotFoundError):
        # FIXME: create proper exception
        print("something is wrong with the backend string")
        raise Exception("Backend String error, cannot load, fix it")

    return backend(uuid=jobdef.uuid)
