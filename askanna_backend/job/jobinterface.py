import json
import random
import string
import uuid

from django.core.exceptions import MultipleObjectsReturned

from job.models import (
    JobInterface,
    JobDef,
    JobRun,
    JobPayload,
    JobOutput,
)


def random_name(length):
    """
    Generate a random string with a given length
    """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


class JobBase(object):
    """
    """
    def __init__(self, uuid=None):
        # property to track if the directly attached JobRun is executed
        # ir we have a placeholder.
        self.dirty = False

        if uuid:
            try:
                jobdef = JobDef.objects.get(uuid=uuid)
            except JobDef.DoesNotExist:
                raise Exception("Custom, no jobdef object found")

            self.jobdef = jobdef

            # Get the active payload for the given JobDef
            try:
                # tmp fix until we have a default payload set
                self.jobpayload = self.jobdef.payload.last()
            except MultipleObjectsReturned:
                raise Exception("Custom: error when attaching the payload, too many objects")

            # Depending on the database design choices, we might force
            # the existence of a jobrun always with a JobDef
            self.jobrun = JobRun.objects.filter(jobdef=self.jobdef).last()

            # we can "pre-allocate" a jobrun to have it available for
            # execution of the next run.
            if not self.jobrun:
                self.jobrun = JobRun.objects.create(jobdef=self.jobdef,
                                                    payload=self.jobpayload)
                # return True # probably a mistake to return bool
                return

            self.dirty = True

        else:
            # create a jobdef object
            jobdef = JobDef.objects.create(name=random_name(8))
            self.jobdef = jobdef

            # new jobdef, so can only have one JobPayload object
            self.jobpayload = jobdef.payload.get()

            jobrun = JobRun.objects.create(jobdef=self.jobdef,
                                           payload=self.jobpayload)
            self.jobrun = jobrun

    def __str__(self):
        return self.jobdef.name

    def _set_payload(self, uuid=None):
        """
        Sets the active JobPayload object related to the JobDef.

        FIXME:
            - should we check here for the status of the active flag in the
            JobPayload ? After all we should only have one active
            payload per jobdef.
        """
        if not uuid:
            # FIXME: this is an exception
            raise Exception("Custom: cannot use this without uuid")

        # check if the uuid passed is for the same payload
        if self.jobpayload.uuid == uuid:
            return True

    def new_payload(self, payload, active=True):
        """
        Allows the addition of a new JobPayload and sets it to active for
        a given JobDef

        FIXME:
            - we can assume that the payload is a python dictionary for now
        """

        # FIXME: this is db implementation specific...
        # _payload = json.dumps(payload)
        if type(payload) != dict:
            raise Exception("Only accept dictionary payloads for now")

        new_payload = JobPayload.objects.create(jobdef=self.jobdef,
                                                payload=payload
                                                owner=self.jobdef.owner)

        # get the current payload object and set active to False
        # also if active is true, attach payload to instance
        if active:
            # replace payload
            self.jobpayload = new_payload

    def _set_payloads(self):
        """
        Get's all the uuids of the payloads that are associated with a given
        JobDef. Used for shortcut functions and reference.
        """
        payloads = []
        for payload in self.jobdef.payload.all():
            payloads.append(payload.uuid)

        self.payloads = payloads

    def _pre_start(self):
        """
        Checks if the state of the JobRun object is dirty.

        We make sure that a new JobRun object is created before we start
        a new run.

        The payload is already set by the JobPayload and JobDef combos.
        """
        if self.dirty:
            new_jobrun = JobRun.objects.create(jobdef=self.jobdef,
                                               payload=self.jobpayload)

            self.jobrun = new_jobrun

    def _pre_get_payload(self):
        """
        Preparation function to extract the payload from the JobPayload.

        Can be overriden if required by backend speficic implementations
        """
        pass

    def get_payload(self):
        """
        Get the payload from the referenced JobPayload object, and make
        it a python object.

        Depends on the type of backend and the way we'll store the payload.
        Currently we use a jsonfield, so assuming serialized to json
        payloads.
        """
        self._pre_get_payload()

        payload = self.jobpayload.payload

        # in case we use SQLite, otherwise the payload should already be a
        # python dictionary
        if type(payload) == str and len(payload) > 0:
            payload = json.loads(payload)

        if payload:
            return payload
        return None

    def get_result(self):
        """
        Generate a result dictionary out of the interfaced models, like:
            JobRun and JobOutput.

        Creates a dictionary with infromation on the state of the job.
        """

        result = {}
        result.update({'status': self.jobrun.status,
                       'cputime': self.jobrun.runtime,
                       'memory': self.jobrun.memory})

        result.update({'return_payload': self.jobrun.output.return_payload,
                       'stdout': self.jobrun.output.stdout,
                       'exit_code': self.jobrun.output.exit_code,
                       'created': self.jobrun.output.created})

        return result
