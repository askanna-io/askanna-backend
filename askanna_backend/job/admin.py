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
    list_display = ['name', 'uuid', 'project', 'created']


@admin.register(JobPayload)
class JobPayloadAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'created']


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'status', 'runtime', 'memory', 'created']


@admin.register(JobOutput)
class JobOutputAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'exit_code', 'created']
