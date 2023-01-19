from django.contrib import admin
from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    fields = [
        "suuid",
        "name",
        "description",
        "visibility",
        "created_by",
        "modified",
        "created",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "created_by",
        "modified",
        "created",
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
        "visibility",
        "created",
        "modified",
        "deleted",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
