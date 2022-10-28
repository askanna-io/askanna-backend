from core.models import Setting
from django.contrib import admin


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "modified"]
    list_display_links = list_display

    date_hierarchy = "created"
    search_fields = ["name"]
