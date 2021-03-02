# -*- coding: utf-8 -*-
from django.contrib import admin

from core.models import Setting


@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ["name", "created", "modified"]
    list_display_links = list_display

    date_hierarchy = "created"
    search_fields = ["name"]

