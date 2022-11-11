from django.contrib import admin
from job.models import JobDef, JobPayload, RunImage, ScheduledJob


@admin.register(JobDef)
class JobDefAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "project",
        "name",
        "description",
        "environment_image",
        "timezone",
        "created",
        "modified",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "environment_image",
        "timezone",
        "created",
        "modified",
    ]
    raw_id_fields = [
        "project",
    ]

    list_display = [
        "suuid",
        "name",
        "project",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "modified",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "project__suuid",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(JobPayload)
class JobPayloadAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "jobdef",
        "lines",
        "size",
        "owner",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "lines",
        "size",
        "modified",
        "created",
    ]
    raw_id_fields = [
        "jobdef",
        "owner",
    ]

    list_display = [
        "suuid",
        "jobdef",
        "project",
        "size",
        "lines",
        "owner",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "jobdef__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.jobdef.project.get_name()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunImage)
class RunImageAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "name",
        "tag",
        "description",
        "digest",
        "cached_image",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "name",
        "tag",
        "digest",
        "cached_image",
        "modified",
        "created",
    ]

    list_display = [
        "name",
        "tag",
        "cached_image",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "name",
        "tag",
        "digest",
        "cached_image",
    ]

    def has_add_permission(self, request):
        return False


@admin.register(ScheduledJob)
class ScheduledJobAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "job",
        "member",
        "raw_definition",
        "cron_definition",
        "cron_timezone",
        "last_run",
        "next_run",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "modified",
        "created",
    ]
    raw_id_fields = [
        "job",
        "member",
    ]

    list_display = [
        "suuid",
        "job_name",
        "project_name",
        "raw_definition",
        "cron_definition",
        "cron_timezone",
        "last_run",
        "next_run",
        "created",
    ]
    date_hierarchy = "next_run"
    list_filter = [
        "last_run",
        "next_run",
        "created",
        "deleted",
    ]
    search_fields = ["suuid", "job__suuid", "raw_definition", "cron_definition", "cron_timezone"]

    def job_name(self, obj):  # pragma: no cover
        return obj.job.get_name()

    def project_name(self, obj):  # pragma: no cover
        return obj.job.project.get_name()

    def has_add_permission(self, request):
        return False
