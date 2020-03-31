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
    list_display = ['name', 'uuid', 'short_uuid', 'function', 'project', 'created']
    list_display_links = ('name', 'uuid', 'short_uuid',)

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]


@admin.register(JobPayload)
class JobPayloadAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobdef', 'created']


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobid', 'jobdef', 'payload', 'status', 'runtime', 'memory', 'created']


@admin.register(JobOutput)
class JobOutputAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'jobdef', 'return_payload', 'exit_code', 'created']
