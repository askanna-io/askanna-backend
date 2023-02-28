from django.contrib import admin
from project.models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid", "workspace", "created_by")}),
        ("Project info", {"fields": ("name", "description", "visibility")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "created_by",
        "modified_at",
        "created_at",
        "deleted_at",
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
        "created_at",
    ]
    list_display_links = (
        "suuid",
        "name",
    )
    date_hierarchy = "created_at"
    list_filter = [
        "visibility",
        "created_at",
        "modified_at",
        "deleted_at",
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
