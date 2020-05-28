# -*- coding: utf-8 -*-
from django.contrib import admin

from job.models import (
    JobArtifact,
    JobDef,
    JobPayload,
    JobRun,
    JobOutput,
)


@admin.register(JobDef)
class JobDefAdmin(admin.ModelAdmin):
    list_display = ["name", "uuid", "short_uuid", "function", "project", "created"]
    list_display_links = (
        "name",
        "uuid",
        "short_uuid",
    )

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]


@admin.register(JobPayload)
class JobPayloadAdmin(admin.ModelAdmin):
    list_display = ["uuid", "jobdef", "created", "owner", "size", "lines"]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]


@admin.register(JobArtifact)
class JobArtifactAdmin(admin.ModelAdmin):
    list_display = ["uuid", "jobrun", "created", "size"]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "jobid",
        "jobdef",
        "payload",
        "status",
        "runtime",
        "memory",
        "created",
        "owner",
    ]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "owner"]


@admin.register(JobOutput)
class JobOutputAdmin(admin.ModelAdmin):
    list_display = ["uuid", "jobdef", "jobrun", "exit_code", "created"]

    date_hierarchy = "created"
    list_filter = ("created", "exit_code")
    search_fields = ["uuid", "short_uuid", "owner"]
