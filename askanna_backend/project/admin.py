from django.contrib import admin

from project.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "uuid",
        "short_uuid",
        "created",
        "modified",
        "deleted",
        "status",
    ]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted", "status")
    search_fields = ["uuid", "short_uuid"]
