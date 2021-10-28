from django.contrib import admin

from project.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "description",
        "short_uuid",
        "status",
        "visibility",
        "created",
        "deleted",
    ]

    list_display_links = (
        "name",
        "short_uuid",
    )

    date_hierarchy = "created"
    list_filter = (
        "created",
        "modified",
        "deleted",
        "status",
        "visibility",
    )
    search_fields = ["uuid", "short_uuid"]
