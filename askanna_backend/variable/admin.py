from django.contrib import admin
from variable.models import Variable


@admin.register(Variable)
class VariableAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("suuid", "project")}),
        ("Variable info", {"fields": ("name", "is_masked")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "project",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    raw_id_fields = [
        "project",
    ]

    list_display = [
        "suuid",
        "project",
        "name",
        "is_masked",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "is_masked",
        "created_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "project__uuid",
        "project__suuid",
        "name",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
