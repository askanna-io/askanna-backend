from django.contrib import admin

# Register your models here.
from django.contrib import admin

from project_template.models import ProjectTemplate


@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "uuid",
        "short_uuid",
        "created",
        "modified",
        "deleted",
        "template_location"

    ]

    list_display_links = ('name', 'uuid', 'short_uuid')

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]
