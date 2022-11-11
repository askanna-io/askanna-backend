from django.contrib import admin
from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
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
        "suuid",
        "created_by",
        "modified",
        "created",
        "activate_date",
        "deactivate_date",
        "deleted",
    ]

    list_display = [
        "suuid",
        "name",
        "visibility",
        "created_by",
        "created",
    ]
    date_hierarchy = "created"
    list_filter = [
        "status",
        "visibility",
        "created",
        "modified",
        "deleted",
    ]
    search_fields = [
        "suuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
