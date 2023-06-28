from django.contrib import admin

from core.models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid")}),
        ("Setting info", {"fields": ("name", "value")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    list_display = [
        "suuid",
        "name",
        "created_at",
        "modified_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "modified_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
    ]
