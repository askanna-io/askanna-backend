from django.contrib import admin
from project.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("suuid", "workspace", "created_by")}),
        ("Project info", {"fields": ("name", "description", "visibility")}),
        ("Important dates", {"fields": ("modified", "created", "deleted")}),
    )
    readonly_fields = [
        "suuid",
        "created_by",
        "modified",
        "created",
        "deleted",
    ]
    raw_id_fields = [
        "workspace",
    ]

    list_display = [
        "suuid",
        "name",
        "visibility",
        "workspace",
        "created_by",
        "created",
    ]
    list_display_links = (
        "suuid",
        "name",
    )
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
        "workspace__uuid",
        "workspace__suuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
