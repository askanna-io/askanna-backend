# -*- coding: utf-8 -*-
import uuid
import random
import string

from celery import group, chain, signature

from flow.models import (
    FlowDef,
    FlowRun,
    FlowInterface,
)

from job.models import get_job


FLOW_TYPE = (
    ('chain', 'chain'),
    ('group', 'group'),
)


def get_flow_pk(pk=None):
    """
    Temp used to retrieve a flow by pk/id
    """
    try:
        flowdef = FlowDef.objects.get(pk=pk)
    except FlowDef.DoesNotExist:
        # FIXME: raise custom proper Exception
        raise Exception(f"get_flow_pk: there is no flowdef with {pk}")

    try:
        flow = CustomFlow(uuid=flowdef.uuid)
    except:
        # FIXME: too general at the moment
        raise Exception(f"get_flow_pk: Cannot initialize CustomFlow with flowdef pk: {pk}")

    return flow


def random_name(length):
    """
    Generate random string with a set length.
    """
    letters = string.ascii_lowercase
    return 'Flow-' + ''.join(random.choice(letters) for i in range(length))


class BaseFlow(FlowInterface):
    """
    Follow similar approach to the Job interface approach.

    We'll try to stay as close to the Job approach as possible, to maintain
    the similar conceptual model, since the goals are quite similar.

    FIXME:
        - the order property of the flow needs to be versioned
        - do we need to associate the Job with the Flow any further than
          the M2M? As in take the specific run of a flow as a given?
    """
    order = []
    flowdef = None
    signatures = None
    ready = False
    flow = None
    dirty = False

    def __init__(self, *args, **kwargs):
        self.uuid = kwargs.get('uuid', None)

        if self.uuid:
            self.flowdef = FlowDef.objects.get(uuid=self.uuid)
        else:
            self.flowdef = FlowDef.objects.create(name=random_name(8))
            self.uuid = self.flowdef.uuid

        self._tasks()

        # Check for flowrun, similarly to jobrun
        self.flowrun = FlowRun.objects.filter(flowdef=self.flowdef).last()

        # we can "pre-allocate" a jobrun to have it available for
        # execution for the next run.
        if not self.flowrun:
            self.flowrun = FlowRun.objects.create(flowdef=self.flowdef)

            #return True
            return

        self.dirty = True
        #return True

    def __str__(self):
        return self.flowdef.__str__()


    def set_order(self, joblist):
        """
        Pass the order of the jobs as a List for the time being.
        """
        if joblist and type(joblist) == list:
            self.order = joblist
        else:
            # FIXME: see if we need to raise an Exception
            print("not possible")

        return self.order


    def _tasks(self):
        _tasks = []
        if self.flowdef:
            for job in self.flowdef.nodes.all():
                # create the signature
                # _job = CeleryJob(uuid=job.uuid)
                _job = get_job(uuid=job.uuid)
                _function = _job._get_function()

                # the Job interface can prepare the proper payload

                # skip payload for now, need to make it more robust
                _tasks.append(_function)

            self.tasks = _tasks

    def order_tasks(self):
        """
        FIXME:
            - need to find an effective strategy for name resolution of tasks,
              so that we are flexible for changes and updates in the future.
              For the time being we use a naive approach, based on naming
              conventions.
        """
        if self.order and self.tasks:
            _tasks = []
            _tasks = [task for x in self.order for task in self.tasks if x in task.name]
            print(_tasks)
            self.tasks = _tasks

            # Ready for start
            self.ready = True

    def set_signatures(self):
        self.signatures = []
        if self.tasks:
            for task in self.tasks:
                # prepare the proper payload, to pass it in the signature
                # FIXME: see how to create the proper signatures here
                _sig = task.s()

                self.signatures.append(_sig)

    def create_flow_sig(self):
        if self.signatures:
            if self.flowdef.flowtype == 'CHAIN':
                self.flow = chain(*self.signatures)
            elif self.flowdef.flowtype == 'GROUP':
                self.flow = group(*self.signatures)

            # Now flow is ready for execution, set dirty to True
            self.dirty = True

    def _pre_start(self):
        """
        Checks if the state of the FlowRun objects is dirty.

        We make sure that a new FlowRun object is created before we start
        a new flowrun.
        """
        if self.dirty:
            new_flowrun = FlowRun.objects.create(flowdef=self.flowdef)
            self.flowrun = new_flowrun

        return self.pre_start()

    def pre_start(self):
        """
        Override if needed
        """
        pass

    def start(self):
        self._pre_start()

        if self.flow:
            ret = self.flow.delay()
            self.ret = ret

    def info(self):
        if self.flow:
            return self.ret.ready()

    def stop(self):
        print("HHHHEEEYYYY SSSTOOOPPPPP")
        if self.flow and not self.ret.ready():
            print("lalalalala")
            print(self.ree)
            self.ret.revoke()

    def kill(self):
        if self.flow and not self.ret.ready():
            self.ret.revoke(terminate=True,
                             signal='SIGKILL')

    def result(self):
        results = {}
        if self.jobs:
            for job in self.jobs:
                results.update({job.name: job.result()})

        return results

class CustomFlow(BaseFlow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._jobs()

    def _jobs(self):
        jobs = []
        if self.flowdef:
            for job in self.flowdef.nodes.all():
                # FIXME: initialize withouth caring of the "type" of Job
                #_job = CeleryJob(uuid=job.uuid)
                _job = get_job(uuid=job.uuid)
                jobs.append(_job)

        self.jobs = jobs

    def order_jobs(self):
        if self.order and self.jobs:
            _jobs = []
            _jobs = [job for x in self.order for job in self.jobs if x in job.name]
            self.jobs = _jobs

            self.ready = True

    #def set_signatures(self):
    #    self.signatures = []
    #    if self.jobs and self.ready:
    #        for job in self.jobs:
    #            job._pre_start()
    #            _task = job._get_function()
    #            _payload = job.get_payload()

    #            task_id = uuid.uuid4()
    #            job.jobrun.jobid = task_id
    #            job.jobrun.status = 'SUBMITTED'
    #            job.jobrun.save()
    #            job.dirty = True

    #            _sig = signature(_task, kwargs=_payload, options={'task_id': task_id})

    #            self.signatures.append(_sig)

    def set_signatures(self):
        """
        Prepares and keeps a list of all the job signatures.
        """
        self.signatures = []
        jobids = []
        if self.jobs and self.ready:
            for job in self.jobs:
                job._make_signature()

                self.signatures.append(job.signature)
                jobids.append(str(job.jobrun.jobid))

        self.flowrun.jobids = jobids
        self.flowrun.save()


    def _temp_order(self):
        order = []

        if self.flowdef.nodes.count() > 0:
            for node in self.flowdef.nodes.order_by('name'):
                order.append(node.name)

        self.order = order


    def pre_start(self):

        self._jobs()

        # 1. set order
        self._temp_order()

        # 2. order tasks
        #self.order_tasks()
        self.order_jobs()

        # 3. create the signatures
        self.set_signatures()

        # 4. create the flow signature
        #self.create_flow_sig()
        # FIXME: see how to pass a custom known task_id for the whole chain
        # need to probably create a FlowRun that will keep the task_id of the
        # included jobs...
        self.create_flow_sig()

