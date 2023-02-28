from core.models import Setting
from django.contrib import admin


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "modified_at"]
    list_display_links = list_display

    date_hierarchy = "created_at"
    search_fields = ["name"]
