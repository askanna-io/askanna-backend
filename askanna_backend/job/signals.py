# -*- coding: utf-8 -*-
import django.dispatch

artifact_upload_finish = django.dispatch.Signal(providing_args=["postheaders"])
result_upload_finish = django.dispatch.Signal(providing_args=["postheaders"])
