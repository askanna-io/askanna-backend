# -*- coding: utf-8 -*-
import uuid

from django.db import models

from job.models import JobDef
from core.fields import JSONField

FLOW_TYPE = (
    ('CHAIN', 'CHAIN'),
    ('GROUP', 'GROUP'),
)

FLOW_STATUS = (
    ('SUBMITTED', 'SUBMITTED'),
    ('COMPLETED', 'COMPLETED'),
    ('PENDING', 'PENDING'),
    ('PAUSED', 'PAUSED'),
    ('IN_PROGRESS', 'IN_PROGRESS'),
    ('FAILED', 'FAILED'),
    ('SUCCESS', 'SUCCESS'),
)

class FlowInterface(object):  # noqa
    """
    Implements main interface towards the Flow interface/concept
    """
    def start(self):
        raise NotImplementedError("This method requires implementation")

    def stop(self):
        raise NotImplementedError("This method requires implementation")

    def reset(self):
        raise NotImplementedError("This method requires implementation")

    def pause(self):
        raise NotImplementedError("This method requires implementation")

    def kill(self):
        raise NotImplementedError("This method requires implementation")

    def info(self):
        raise NotImplementedError("This method requires implementation")

    def status(self):
        raise NotImplementedError("This method requires implementation")

    def result(self):
        raise NotImplementedError("This method requires implementation")

    def addjob(self):
        raise NotImplementedError("This method requires implementation")

    def remjob(self):
        raise NotImplementedError("This method requires implementation")


class FlowDef(models.Model):
    """
    Similar to the JobDef, this stores the identity of the Flow.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    name = models.CharField(max_length=50)
    project = models.CharField(max_length=30, blank=True, null=True)
    flowtype = models.CharField(max_length=50, choices=FLOW_TYPE,
                                default='CHAIN')

    # FIXME: may be replaced by model_utils and TimeStampedModel if required
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    visible = models.BooleanField(default=True)  # FIXME: add rationale and default value

    # FIXME: should we kink to the jobdef?
    nodes = models.ManyToManyField('job.JobDef', blank=True)
    edgelist = models.TextField(blank=True, null=True)
    graph = JSONField(blank=True, null=True)

    # FIXME: will probably change once we have the permission system
    # figured out.
    owner = models.CharField(max_length=100, blank=True, null=True)

    version = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Flow Definition'
        verbose_name_plural = 'Flow Definitions'


class FlowRun(models.Model):
    """
    Similar to the JobRun, this stores the specifics of any run for
    a given FlowDef.
    """
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    flowdef = models.ForeignKey('flow.FlowDef', on_delete=models.CASCADE,
                                to_field='uuid', related_name='flowruns')
    status = models.CharField(max_length=20, choices=FLOW_STATUS)

    # the jobids of the jobs included in the flowdef
    # TODO: check if we should keep a list of the jobids, or make
    # relationships. rather keep it simple for now
    jobids = JSONField(blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)

    # FIXME: see what name to use since there might be a conflict with
    # the permission system.
    # FIXME: replace with reference to User Object.
    owner = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Flow Run'
        verbose_name_plural = 'Flow Runs'
