# -*- coding: utf-8 -*-
from django.contrib import admin

from job.models import (
    JobDef,
    JobPayload,
    JobRun,
    JobOutput,
)


@admin.register(JobDef)
class JobDefAdmin(admin.ModelAdmin):
    list_display = ['name', 'uuid', 'function', 'project', 'created']


@admin.register(JobPayload)
class JobPayloadAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobdef', 'created']


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobid', 'jobdef', 'payload', 'status', 'runtime', 'memory', 'created']


@admin.register(JobOutput)
class JobOutputAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobdef', 'return_payload', 'exit_code', 'created']
