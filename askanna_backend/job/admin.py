# -*- coding: utf-8 -*-
from django.contrib import admin

from job.models import (
    ChunkedJobOutputPart,
    ChunkedArtifactPart,
    JobArtifact,
    JobDef,
    JobOutput,
    JobPayload,
    JobRun,
    JobVariable,
    RunMetrics,
)

admin.site.register(ChunkedJobOutputPart)
admin.site.register(ChunkedArtifactPart)


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
        "created",
        "owner",
        "member",
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


@admin.register(JobVariable)
class JobVariableAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "short_uuid",
        "name",
        "project",
        "created",
    ]
    list_display_links = (
        "name",
        "uuid",
        "short_uuid",
    )

    date_hierarchy = "created"
    list_filter = ("created",)
    search_fields = ["uuid", "short_uuid", "name"]


@admin.register(RunMetrics)
class RunMetricsAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "short_uuid",
        "count",
        "size",
    ]
    list_display_links = (
        "uuid",
        "short_uuid",
    )

    raw_id_fields = ["jobrun"]
    search_fields = ["uuid", "uuid__short_uuid"]
