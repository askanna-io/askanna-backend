from django.contrib import admin
from job.models import (
    ChunkedArtifactPart,
    JobArtifact,
    JobDef,
    JobOutput,
    JobPayload,
    JobRun,
    JobVariable,
    RunImage,
    RunMetrics,
    RunMetricsRow,
    RunResult,
    RunVariableRow,
    RunVariables,
    ScheduledJob,
)


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
    list_display = ["uuid", "jobrun", "size", "count_dir", "count_files", "created"]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]
    raw_id_fields = ["jobrun"]

    fields = [
        "short_uuid",
        "size",
        "count_dir",
        "count_files",
        "jobrun",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "short_uuid",
        "size",
        "count_dir",
        "count_files",
        "modified",
        "created",
        "deleted",
    ]


@admin.register(ChunkedArtifactPart)
class ChunkedArtifactPartAdmin(admin.ModelAdmin):
    list_display = ["uuid", "artifact", "created", "size"]
    date_hierarchy = "created"
    list_filter = ("created", "deleted")
    search_fields = ["uuid", "short_uuid", "artifact__uuid", "artifact__short_uuid"]
    raw_id_fields = ["artifact"]


@admin.register(JobRun)
class JobRunAdmin(admin.ModelAdmin):
    def project(obj):  # pragma: no cover
        return obj.jobdef.project.get_name()

    def job_name(obj):  # pragma: no cover
        return obj.jobdef.get_name()

    def job_suuid(obj):  # pragma: no cover
        return obj.jobdef.short_uuid

    fields = (
        "short_uuid",
        "jobdef",
        "jobid",
        "status",
        "trigger",
        "started",
        "finished",
        "duration",
        "name",
        "description",
        "package",
        "created_by",
        "member",
        "payload",
        "environment_name",
        "run_image",
        "timezone",
        "modified",
        "created",
        "deleted",
    )
    readonly_fields = [
        "short_uuid",
        "jobid",
        "trigger",
        "started",
        "finished",
        "duration",
        "environment_name",
        "timezone",
        "modified",
        "created",
    ]
    raw_id_fields = (
        "jobdef",
        "package",
        "created_by",
        "member",
        "payload",
        "run_image",
    )

    list_display = [
        "short_uuid",
        project,
        job_name,
        job_suuid,
        "status",
        "created",
        "started",
        "finished",
        "created_by",
    ]
    date_hierarchy = "created"
    list_filter = (
        "status",
        "created",
        "started",
        "finished",
        "deleted",
    )
    search_fields = [
        "short_uuid",
        "jobdef__short_uuid",
        "jobdef__name",
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
    fields = (
        "jobrun",
        "count",
        "size",
        "metric_names",
        "label_names",
        "modified",
        "created",
        "deleted",
    )
    list_display = [
        "short_uuid",
        "count",
        "size",
        "created",
    ]
    list_display_links = ("short_uuid",)
    readonly_fields = [
        "count",
        "size",
        "metric_names",
        "label_names",
        "modified",
        "created",
    ]
    raw_id_fields = ["jobrun"]
    list_filter = ("created",)
    search_fields = ["jobrun__short_uuid"]


@admin.register(RunMetricsRow)
class RunMetricsRowAdmin(admin.ModelAdmin):
    fields = (
        "run_suuid",
        "metric",
        "label",
        "modified",
        "created",
        "deleted",
    )
    list_display = [
        "run_suuid",
        "metric",
        "label",
        "created",
    ]
    list_display_links = ("run_suuid",)
    readonly_fields = [
        "run_suuid",
        "metric",
        "label",
        "modified",
        "created",
    ]
    list_filter = ("created",)
    search_fields = ["run_suuid"]


@admin.register(RunVariables)
class RunVariablesAdmin(admin.ModelAdmin):
    fields = (
        "jobrun",
        "count",
        "size",
        "variable_names",
        "label_names",
        "modified",
        "created",
        "deleted",
    )
    list_display = [
        "short_uuid",
        "count",
        "size",
        "created",
    ]
    list_display_links = ("short_uuid",)
    readonly_fields = [
        "count",
        "size",
        "variable_names",
        "label_names",
        "modified",
        "created",
    ]
    raw_id_fields = ["jobrun"]
    list_filter = ("created",)
    search_fields = ["jobrun__short_uuid"]


@admin.register(RunVariableRow)
class RunVariableRowAdmin(admin.ModelAdmin):
    fields = (
        "run_suuid",
        "variable",
        "is_masked",
        "label",
        "modified",
        "created",
        "deleted",
    )
    list_display = [
        "run_suuid",
        "variable",
        "is_masked",
        "label",
        "created",
    ]
    list_display_links = ("run_suuid",)
    readonly_fields = [
        "run_suuid",
        "variable",
        "is_masked",
        "label",
        "modified",
        "created",
    ]
    list_filter = ("created",)
    search_fields = ["run_suuid"]
