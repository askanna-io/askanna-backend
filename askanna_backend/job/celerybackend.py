from django.db.transaction import on_commit

from config.celery_app import app as celery_application
from celery.signals import (
    task_prerun,
    task_postrun,
    after_task_publish,
    task_success,
    task_failure,
)
from celery.utils import uuid as celuuid
from celery import signature
from django_celery_results.models import TaskResult

from job.jobinterface import JobBase
from job.models import JobInterface, JobRun


# FIXME: Slight hack to make sure that the celery task registry has been
# properly populated with all the tasks from the different apps. By
# default the autodiscover uses a lazy approach, so we force the discover
# to make sure we have the registry populated. Need to find a better way
# to do this :)
celery_application.autodiscover_tasks(force=True)


import logging
celery_logger = logging.getLogger('celery')


class CeleryJob(JobInterface, JobBase):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    def __str__(self):
        return self.jobdef.__str__()

    @property
    def name(self):
        if self.jobdef:
            return self.jobdef.name
        else:
            return 'none'

    def _get_function(self):
        """
        Check to see if the function name in the JobDef is part of the
        registered tasks of Celery. to do the check, we use the app instance
        from the celery config file.
        """
        tasks = celery_application.tasks

        task = tasks.get(self.jobdef.function, None)

        if not task:
            raise Exception('No task with name: {}'.format(self.jobdef.function))

        return task

    def _make_signature(self):
        """
        Create custom signature for the function and the payload that
        are associated with the given JobDef.

        We want to set our own uuid for the celery task.
        """

        # make sure we have a fresh jobrun
        self._pre_start()

        task = self._get_function()
        payload = self.get_payload()

        # TODO: this is replaced, so that we can set a known uuid for the
        # celery task from our side, when creating the signature.
        #if payload:
        #    signature = task.s(**payload)
        #else:
        #    signature = task.s()
        task_id = celuuid()
        self.jobid = task_id

        _signature = signature(task,
                               kwargs=payload,
                               options={'task_id': self.jobid})

        # attach it to instance
        self.signature = _signature

        # Update the jobrun
        self.jobrun.jobid = self.jobid
        self.jobrun.status = 'PENDING'
        self.jobrun.save()

        # jobrun in use, so mark dirty
        self.dirty = True


    def start(self):
        #self._pre_start()
        self._make_signature()

        # deals with db race conditions
        # https://celery.readthedocs.io/en/latest/userguide/tasks.html#database-transactions
        on_commit(lambda: self.signature.delay())

        # store the id of the celery task
        #self.jobrun.jobid = celery_task.id
        #self.jobrun.status = 'SUBMITTED'
        #self.jobrun.save()
        #self.dirty = True

    def stop(self):
        """
        Given the jobid of the celery process stored in the JobRun, we can
        use the celery_application reference to revoke the specific job.

        NOTE:
            the behavior of the the stop, depends on the pool system that we
            use (prefork, eventlet, gevent)

            See also: https://celery.readthedocs.io/en/latest/userguide/workers.html?highlight=pool#commands
        """
        # FIXME: define exceptions and handling process
        try:
            celery_job = self.jobrun.jobid
        except:
            celery_job = None

        if celery_job:
            celery_application.control.revoke(celery_job)

    def kill(self):
        """
        When revoking we have the option to pass signals supported by the
        `signal` module of Python.

        See:
            - https://docs.python.org/dev/library/signal.html#module-signal
            - https://celery.readthedocs.io/en/latest/userguide/workers.html?highlight=pool#revoke-revoking-tasks
        """
        # FIXME: define exceptions and handling process
        try:
            celery_job = self.jobrun.jobid
        except:
            celery_job = None

        if celery_job:
            celery_application.control.revoke(celery_job,
                                              terminate=True,
                                              signal='SIGKILL')

    def info(self):
        """
        Returns a complete information dictionary, providing full description
        of the JobDef and the attached last instances of JobPayload, JobRun
        and JobOutput objects.

        This is the method that adds the complete context to the Job.

        FIXME:
            - check to see if we can use some serialization method from
              Django or DRF
        """
        info = {
            'name': self.jobdef.name,
            'project': self.jobdef.project.uuid,
            'function': self.jobdef.function,
            'backend': self.jobdef.backend,
            'created': self.jobdef.created,
            'payload': self.jobpayload.payload,
            'lastrun': {
                'status': self.jobrun.status,
                'runtime': self.jobrun.runtime,
                'memory': self.jobrun.memory,
                'return_payload': self.jobrun.output.return_payload,
                'stdout': self.jobrun.output.stdout,
                'created': self.jobrun.created,
                'finished': self.jobrun.output.created
            },
        }
        return info

    def result(self):
        """
        Returns the output of the last JobRun associated with the specified
        JobDef.
        """
        if self.jobrun.output:
            # FIXME: find a more efficient way to do this
            # make sure we have the "refreshed" object from the DB
            self.jobrun.output.refresh_from_db()
            #return self.jobrun.output.return_payload
            return self.get_result()
        else:
            # FIXME: see what a proper "empty" return value should be
            return 'None'

    def status(self):
        """
        Returns the status of the last JobRun associated with the specified
        JobDef.
        """
        return self.jobrun.status

    def runs(self):
        """
        Returns queryset of all JobRun objects associated with the specified
        JobDef.
        """
        return JobRun.objects.filter(jobdef=self.jobdef)


@task_prerun.connect
def update_prerun_jobrun(sender=None, headers=None, body=None, **kwargs):
    task_id = kwargs.get('task_id', None)
    if task_id:
        print(f"TaskID: {task_id}")
        jobrun = JobRun.objects.get(jobid=task_id)
        jobrun.status = 'SUBMITTED'
        jobrun.save()


@task_failure.connect
def update_failed_jobrun(sender=None, headers=None, body=None, **kwargs):
    task_id = kwargs.get('task_id', None)
    if task_id:
        jobrun = JobRun.objects.get(jobid=task_id)
        jobrun.status = 'FAILED'
        jobrun.save()

        task_result = TaskResult.objects.get(task_id=task_id)
        jobrun.output.return_payload = task_result.result
        if task_result.traceback:
            jobrun.output.stdout = task_result.traceback
        jobrun.output.save()


@task_postrun.connect
def update_postrun_jobrun(sender=None, headers=None, body=None, **kwargs):
    task_id = kwargs.get('task_id', None)
    jobrun = JobRun.objects.get(jobid=task_id)
    state = kwargs.get('state', 'FAILED')
    jobrun.status = state

    task_result = TaskResult.objects.get(task_id=task_id)
    calc_time = (task_result.date_done - jobrun.created).total_seconds()
    jobrun.runtime = calc_time
    jobrun.save()

    # Get the results from the jobs
    jobrun.output.return_payload = task_result.result
    if task_result.traceback:
        jobrun.output.stdout = task_result.traceback

    #update the execution time
    jobrun.output.created = task_result.date_done
    jobrun.output.save()


@after_task_publish.connect
def testing_celery_signals(sender=None, headers=None, body=None, **kwargs):
    celery_logger.info("task publish Hello, it works")


@task_success.connect
def testing_celery_signal_success(sender=None, headers=None, body=None, **kwargs):
    celery_logger.info("success Hello, it works")

