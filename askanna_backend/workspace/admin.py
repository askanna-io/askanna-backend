from django.contrib import admin

from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "short_uuid",
        "status",
        "visibility",
        "created",
        "deleted",
    ]
    list_display_links = list_display
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
    ]
