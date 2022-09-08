from django.contrib import admin
from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = [
        "short_uuid",
        "name",
        "description",
        "visibility",
        "created_by",
        "created",
        "deleted",
    ]
    list_display_links = [
        "short_uuid",
        "name",
    ]
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
    ]
    fields = [
        "short_uuid",
        "status",
        "name",
        "description",
        "visibility",
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

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
