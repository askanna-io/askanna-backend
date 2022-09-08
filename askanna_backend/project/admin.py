from django.contrib import admin
from project.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "short_uuid",
        "name",
        "description",
        "visibility",
        "workspace",
        "created_by",
        "created",
        "deleted",
    ]
    list_display_links = (
        "short_uuid",
        "name",
    )
    date_hierarchy = "created"
    list_filter = (
        "created",
        "modified",
        "deleted",
        "status",
        "visibility",
    )
    search_fields = [
        "uuid",
        "short_uuid",
        "name",
        "workspace__short_uuid",
        "workspace__name",
    ]
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
    raw_id_fields = ["workspace"]
    readonly_fields = [
        "short_uuid",
        "created_by",
        "modified",
        "created",
        "activate_date",
        "deactivate_date",
        "deleted",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
