from django.contrib import admin

from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "created",
    ]
    list_display_links = list_display
    date_hierarchy = "created"
    list_filter = (
        "created",
        "modified",
        "deleted",
    )
    search_fields = [
        "uuid",
        "short_uuid",
    ]
