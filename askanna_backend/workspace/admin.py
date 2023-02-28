from django.contrib import admin
from workspace.models import Workspace


@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid", "created_by")}),
        ("Workspace info", {"fields": ("name", "description", "visibility")}),
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

    list_display = [
        "suuid",
        "name",
        "visibility",
        "created_by",
        "created_at",
    ]
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
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
