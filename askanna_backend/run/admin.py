import json

from django.contrib import admin
from django.template.defaultfilters import truncatechars
from run.models import (
    Run,
    RunArtifact,
    RunLog,
    RunMetric,
    RunMetricMeta,
    RunResult,
    RunVariable,
    RunVariableMeta,
)


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "jobdef",
        "jobid",
        "status",
        "trigger",
        "started_at",
        "finished_at",
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
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "jobid",
        "trigger",
        "started_at",
        "finished_at",
        "duration",
        "environment_name",
        "timezone",
        "modified_at",
        "created_at",
    ]
    raw_id_fields = [
        "jobdef",
        "package",
        "created_by",
        "member",
        "payload",
        "run_image",
    ]

    list_display = [
        "suuid",
        "name",
        "job_name",
        "project",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "created_by",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
        "jobdef_uuid",
        "jobdef__suuid",
        "jobdef__name",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.jobdef.project.name

    def job_name(self, obj):  # pragma: no cover
        return obj.jobdef.name

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunArtifact)
class RunArtifactAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "run",
        "size",
        "count_dir",
        "count_files",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "size",
        "count_dir",
        "count_files",
        "modified_at",
        "created_at",
    ]
    raw_id_fields = [
        "run",
    ]

    list_display = [
        "suuid",
        "run",
        "job_name",
        "project",
        "count_dir",
        "count_files",
        "size",
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
        "run__uuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.name

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.name

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunLog)
class RunLogAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "run",
        "exit_code",
        "lines",
        "size",
        "log_preview",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "exit_code",
        "lines",
        "size",
        "log_preview",
        "modified_at",
        "created_at",
    ]
    raw_id_fields = [
        "run",
    ]

    list_display = [
        "suuid",
        "run",
        "job_name",
        "project",
        "exit_code",
        "lines",
        "size",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "exit_code",
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "run__uuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.name

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.name

    def log_preview(self, obj):  # pragma: no cover
        if obj.lines > 50:
            log_first = json.dumps(obj.stdout[:20], indent=4)
            log_last = json.dumps(obj.stdout[-20:], indent=4)
            return f"{log_first} \n\n...\n\n {log_last}"
        else:
            return json.dumps(obj.stdout, indent=4)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunResult)
class RunResultAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "run",
        "name",
        "size",
        "extension",
        "mime_type",
        "description",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "name",
        "size",
        "extension",
        "mime_type",
        "modified_at",
        "created_at",
    ]
    raw_id_fields = [
        "run",
    ]

    list_display = [
        "suuid",
        "run",
        "job_name",
        "project",
        "size",
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
        "run__uuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.name

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.name

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunMetricMeta)
class RunMetricMetaAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "run",
        "job_name",
        "count",
        "size",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "run__uuid",
        "run__suuid",
    ]

    fieldsets = (
        (None, {"fields": ("suuid", "run", "job_name", "project_name", "workspace_name")}),
        ("Metrics meta", {"fields": ("count", "size", "metric_names", "label_names")}),
        ("Important dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "run",
        "count",
        "size",
        "metric_names",
        "label_names",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef

    def project_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project

    def workspace_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.workspace

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunMetric)
class RunMetricAdmin(admin.ModelAdmin):
    list_display = [
        "run",
        "job_name",
        "metric_preview",
        "label_preview",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "run__uuid",
        "run__suuid",
        "run__jobdef__uuid",
        "run__jobdef__suuid",
        "run__jobdef__project__uuid",
        "run__jobdef__project__suuid",
        "run__jobdef__project__workspace__uuid",
        "run__jobdef__project__workspace__suuid",
    ]

    fieldsets = (
        (None, {"fields": ("run", "job_name", "project_name", "workspace_name")}),
        ("Metric", {"fields": ("metric", "label")}),
        ("Important dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "run",
        "job_name",
        "project_name",
        "workspace_name",
        "metric",
        "label",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef

    def project_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project

    def workspace_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.workspace

    def metric_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.metric, 100)

    def label_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.label, 100)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunVariableMeta)
class RunVariableMetaAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "run",
        "job_name",
        "count",
        "size",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "run__uuid",
        "run__suuid",
    ]

    fieldsets = (
        (None, {"fields": ("suuid", "run", "job_name", "project_name", "workspace_name")}),
        ("Variables meta", {"fields": ("count", "size", "variable_names", "label_names")}),
        ("Important dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "run",
        "count",
        "size",
        "variable_names",
        "label_names",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef

    def project_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project

    def workspace_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.workspace

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunVariable)
class RunVariableAdmin(admin.ModelAdmin):
    list_display = [
        "run",
        "job_name",
        "variable_preview",
        "is_masked",
        "label_preview",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "is_masked",
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "run__uuid",
        "run__suuid",
        "run__jobdef__uuid",
        "run__jobdef__suuid",
        "run__jobdef__project__uuid",
        "run__jobdef__project__suuid",
        "run__jobdef__project__workspace__uuid",
        "run__jobdef__project__workspace__suuid",
    ]

    fieldsets = (
        (None, {"fields": ("run", "job_name", "project_name", "workspace_name")}),
        ("Metric", {"fields": ("variable", "is_masked", "label")}),
        ("Important dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "run",
        "job_name",
        "project_name",
        "workspace_name",
        "variable",
        "is_masked",
        "label",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef

    def project_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project

    def workspace_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.workspace

    def variable_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.variable, 100)

    def label_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.label, 100)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
