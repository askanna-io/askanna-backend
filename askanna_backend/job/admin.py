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
        "created_at",
        "modified_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "environment_image",
        "timezone",
        "created_at",
        "modified_at",
    ]
    raw_id_fields = [
        "project",
    ]

    list_display = [
        "suuid",
        "name",
        "project",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "modified_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
        "project__suuid",
        "project__workspace__suuid",
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
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "lines",
        "size",
        "modified_at",
        "created_at",
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
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "jobdef__uuid",
        "jobdef__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.jobdef.project.name

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
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "name",
        "tag",
        "digest",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    list_display = [
        "name",
        "tag",
        "cached_image",
        "modified_at",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
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
        "last_run_at",
        "next_run_at",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "modified_at",
        "created_at",
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
        "last_run_at",
        "next_run_at",
        "created_at",
    ]
    date_hierarchy = "next_run_at"
    list_filter = [
        "last_run_at",
        "next_run_at",
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "job__suuid",
        "raw_definition",
        "cron_definition",
        "cron_timezone",
    ]

    def job_name(self, obj):  # pragma: no cover
        return obj.job.name

    def project_name(self, obj):  # pragma: no cover
        return obj.job.project.name

    def has_add_permission(self, request):
        return False
