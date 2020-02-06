# -*- coding: utf-8 -*-
from django.contrib import admin

from flow.models import (
    FlowDef,
    FlowRun,
)

@admin.register(FlowDef)
class FlowDefAdmin(admin.ModelAdmin):
    list_display = ['name', 'uuid', 'project', 'created']


@admin.register(FlowRun)
class FlowRunAdmin(admin.ModelAdmin):
    list_display = ['uuid', 'flowdef', 'status', 'created']
