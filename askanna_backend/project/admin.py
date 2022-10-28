from django.contrib import admin
from project.models import Project, ProjectVariable


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fields = [
        "short_uuid",
        "status",
        "name",
        "description",
        "visibility",
        "workspace",
        "created_by",
        "modified",
        "created",
        "activate_date",
        "deactivate_date",
        "deleted",
    ]
    readonly_fields = [
        "short_uuid",
        "created_by",
        "modified",
        "created",
        "activate_date",
        "deactivate_date",
        "deleted",
    ]
    raw_id_fields = [
        "workspace",
    ]

    list_display = [
        "short_uuid",
        "name",
        "visibility",
        "workspace",
        "created_by",
        "created",
    ]
    list_display_links = (
        "short_uuid",
        "name",
    )
    date_hierarchy = "created"
    list_filter = [
        "status",
        "visibility",
        "created",
        "modified",
        "deleted",
    ]
    search_fields = [
        "short_uuid",
        "workspace__short_uuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ProjectVariable)
class ProjectVariableAdmin(admin.ModelAdmin):
    fields = [
        "short_uuid",
        "project",
        "name",
        "value",
        "is_masked",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "short_uuid",
        "project",
        "modified",
        "created",
    ]
    raw_id_fields = [
        "project",
    ]

    list_display = [
        "short_uuid",
        "project",
        "name",
        "is_masked",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "is_masked",
        "created",
        "deleted",
    ]
    search_fields = [
        "short_uuid",
        "project__short_uuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
