# -*- coding: utf-8 -*-
from django.contrib import admin

from job.models import (
    ChunkedArtifactPart,
    JobArtifact,
    JobDef,
    JobOutput,
    JobPayload,
    JobRun,
    JobVariable,
    ScheduledJob,
    RunMetrics,
    RunMetricsRow,
    RunImage,
    RunResult,
    RunVariables,
    RunVariableRow,
)

admin.site.register(ChunkedArtifactPart)


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    def jobname(obj):  # pragma: no cover
        return obj.job.name

    def project(obj):  # pragma: no cover
        return obj.job.project.get_name()

    def membername(obj):  # pragma: no cover
        return obj.member.get_name()

    list_display = [
        project,
        jobname,
        "raw_definition",
        "cron_definition",
        "cron_timezone",
        membername,
        "last_run",
        "next_run",
        "created",
    ]

    list_display_links = (
        project,
        jobname,
    )

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid", "cron_definition", "cron_timezone"]


@admin.register(JobDef)
class JobDefAdmin(admin.ModelAdmin):
    list_display = ["name", "uuid", "short_uuid", "project", "created"]
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
    def project(obj):  # pragma: no cover
        return obj.jobdef.project.get_name()

    def jobname(obj):  # pragma: no cover
        return obj.jobdef.get_name()

    def job_suuid(obj):  # pragma: no cover
        return obj.jobdef.short_uuid

    def payload_suuid(obj):  # pragma: no cover
        if obj.payload:
            return obj.payload.short_uuid
        return ""

    list_display = [
        "short_uuid",
        project,
        jobname,
        job_suuid,
        payload_suuid,
        "status",
        "created",
        "started",
        "modified",
        "owner",
    ]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = [
        "short_uuid",
        "owner",
        "jobdef__short_uuid",
        "jobdef__name",
        "payload__short_uuid",
    ]


@admin.register(JobOutput)
class JobOutputAdmin(admin.ModelAdmin):
    list_display = ["uuid", "jobdef", "jobrun", "exit_code", "created"]

    date_hierarchy = "created"
    list_filter = ("created", "exit_code")
    search_fields = ["uuid", "short_uuid", "owner"]


@admin.register(RunImage)
class RunImageAdmin(admin.ModelAdmin):
    list_display = ["name", "tag", "digest", "cached_image", "created"]

    date_hierarchy = "created"
    list_filter = ("created",)
    search_fields = ["name", "tag", "cached_image"]


@admin.register(RunResult)
class RunResultAdmin(admin.ModelAdmin):
    list_display = ["uuid", "job", "run", "created"]

    date_hierarchy = "created"
    list_filter = ("created",)
    search_fields = ["uuid", "short_uuid", "job"]


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
        "jobrun",
        "short_uuid",
        "count",
        "size",
    ]
    list_display_links = (
        "jobrun",
        "short_uuid",
    )

    raw_id_fields = ["jobrun"]
    search_fields = ["jobrun__short_uuid"]


@admin.register(RunMetricsRow)
class RunMetricsRowAdmin(admin.ModelAdmin):
    list_display = [
        "project_suuid",
        "job_suuid",
        "run_suuid",
        "short_uuid",
        "metric",
        "label",
    ]
    list_display_links = (
        "project_suuid",
        "job_suuid",
        "run_suuid",
    )

    search_fields = [
        "project_suuid",
        "job_suuid",
        "run_suuid",
    ]


@admin.register(RunVariables)
class RunVariablesAdmin(admin.ModelAdmin):
    list_display = [
        "jobrun",
        "short_uuid",
        "count",
        "size",
    ]
    list_display_links = (
        "jobrun",
        "short_uuid",
    )

    raw_id_fields = ["jobrun"]
    search_fields = ["jobrun__short_uuid"]


@admin.register(RunVariableRow)
class RunVariableRowAdmin(admin.ModelAdmin):
    list_display = [
        "project_suuid",
        "job_suuid",
        "run_suuid",
        "short_uuid",
        "variable",
        "is_masked",
        "label",
    ]
    list_display_links = (
        "project_suuid",
        "job_suuid",
        "run_suuid",
    )

    search_fields = [
        "project_suuid",
        "job_suuid",
        "run_suuid",
    ]
