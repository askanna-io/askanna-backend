from django.contrib import admin
from django.template.defaultfilters import truncatechars

from run.models import Run, RunArtifact, RunMetric, RunVariable


@admin.register(Run)
class RunAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid", "jobdef", "created_by_member")}),
        (
            "Run info",
            {
                "fields": (
                    "name",
                    "description",
                    "status",
                    "exit_code",
                    "duration",
                )
            },
        ),
        (
            "Metadata",
            {
                "fields": (
                    "package",
                    "trigger",
                    "log_file",
                    "payload_file",
                    "result_file",
                    "metrics_file",
                    "metrics_meta",
                    "variables_file",
                    "variables_meta",
                    "environment_name",
                    "run_image",
                    "timezone",
                )
            },
        ),
        ("Dates", {"fields": ("started_at", "finished_at", "modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "jobdef",
        "created_by_member",
        "duration",
        "package",
        "trigger",
        "log_file",
        "payload_file",
        "result_file",
        "metrics_file",
        "metrics_meta",
        "variables_file",
        "variables_meta",
        "environment_name",
        "run_image",
        "timezone",
        "started_at",
        "finished_at",
        "modified_at",
        "created_at",
    ]

    list_display = [
        "suuid",
        "name",
        "jobdef",
        "project",
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "created_by_member",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "status",
        "created_at",
        "started_at",
        "finished_at",
        "modified_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
        "jobdef__uuid",
        "jobdef__suuid",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunArtifact)
class RunArtifactAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid", "run")}),
        ("Artifact info", {"fields": ("artifact_file",)}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "run",
        "artifact_file",
        "modified_at",
        "created_at",
    ]

    list_display = [
        "suuid",
        "run",
        "job",
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
        "run__uuid",
        "run__suuid",
        "run__jobdef__uuid",
        "run__jobdef__suuid",
        "run__jobdef__project__uuid",
        "run__jobdef__project__suuid",
        "run__jobdef__project__workspace__uuid",
        "run__jobdef__project__workspace__suuid",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(RunMetric)
class RunMetricAdmin(admin.ModelAdmin):
    list_display = [
        "run",
        "job",
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
        (None, {"fields": ("run", "job", "project", "workspace")}),
        ("Metric", {"fields": ("metric", "label")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "run",
        "job",
        "project",
        "workspace",
        "metric",
        "label",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job(self, obj):
        return obj.run.jobdef

    def project(self, obj):
        return obj.run.jobdef.project

    def workspace(self, obj):
        return obj.run.jobdef.project.workspace

    def metric_preview(self, obj):
        return truncatechars(obj.metric, 100)

    def label_preview(self, obj):
        return truncatechars(obj.label, 100)

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
        "job",
        "variable_preview",
        "is_masked",
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
        (None, {"fields": ("run", "job", "project", "workspace")}),
        ("Variable", {"fields": ("variable", "is_masked", "label")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "run",
        "job",
        "project",
        "workspace",
        "variable",
        "is_masked",
        "label",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def job(self, obj):
        return obj.run.jobdef

    def project(self, obj):
        return obj.run.jobdef.project

    def workspace(self, obj):
        return obj.run.jobdef.project.workspace

    def variable_preview(self, obj):
        return truncatechars(obj.variable, 100)

    def label_preview(self, obj):
        return truncatechars(obj.label, 100)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
