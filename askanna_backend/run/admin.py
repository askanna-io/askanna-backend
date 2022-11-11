import json

from django.contrib import admin
from django.template.defaultfilters import truncatechars
from run.models import (
    Run,
    RunArtifact,
    RunLog,
    RunMetric,
    RunMetricRow,
    RunResult,
    RunVariable,
    RunVariableRow,
)


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
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
    ]
    readonly_fields = [
        "suuid",
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
        "created",
        "started",
        "finished",
        "created_by",
    ]
    date_hierarchy = "created"
    list_filter = [
        "status",
        "created",
        "started",
        "finished",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "name",
        "jobdef__suuid",
        "jobdef__name",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.jobdef.get_name()

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
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "size",
        "count_dir",
        "count_files",
        "modified",
        "created",
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
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.get_name()

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
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "exit_code",
        "lines",
        "size",
        "log_preview",
        "modified",
        "created",
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
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "exit_code",
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.get_name()

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
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "name",
        "size",
        "extension",
        "mime_type",
        "modified",
        "created",
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
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.get_name()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunMetric)
class RunMetricAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "run",
        "count",
        "size",
        "metric_names",
        "label_names",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "count",
        "size",
        "metric_names",
        "label_names",
        "modified",
        "created",
    ]
    raw_id_fields = [
        "run",
    ]

    list_display = [
        "suuid",
        "run",
        "job_name",
        "project",
        "count",
        "size",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.get_name()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunMetricRow)
class RunMetricRowAdmin(admin.ModelAdmin):
    fields = [
        "run_suuid",
        "job_suuid",
        "project_suuid",
        "metric",
        "label",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "run_suuid",
        "job_suuid",
        "project_suuid",
        "metric",
        "label",
        "modified",
        "created",
    ]

    list_display = [
        "run_suuid",
        "metric_preview",
        "label_preview",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "run_suuid",
        "job_suuid",
        "project_suuid",
    ]

    def metric_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.metric, 100)

    def label_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.label, 100)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunVariable)
class RunVariableAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "run",
        "count",
        "size",
        "variable_names",
        "label_names",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "count",
        "size",
        "variable_names",
        "label_names",
        "modified",
        "created",
    ]
    raw_id_fields = [
        "run",
    ]

    list_display = [
        "suuid",
        "run",
        "job_name",
        "project",
        "count",
        "size",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "created",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "run__suuid",
    ]

    def project(self, obj):  # pragma: no cover
        return obj.run.jobdef.project.get_name()

    def job_name(self, obj):  # pragma: no cover
        return obj.run.jobdef.get_name()

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunVariableRow)
class RunVariableRowAdmin(admin.ModelAdmin):
    fields = [
        "run_suuid",
        "variable",
        "is_masked",
        "label",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "run_suuid",
        "variable",
        "is_masked",
        "label",
        "modified",
        "created",
    ]

    list_display = [
        "run_suuid",
        "variable_preview",
        "is_masked",
        "label_preview",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "is_masked",
        "created",
        "deleted",
    ]
    search_fields = [
        "run_suuid",
    ]

    def variable_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.variable, 100)

    def label_preview(self, obj):  # pragma: no cover
        return truncatechars(obj.label, 100)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
