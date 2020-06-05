# Generated by Django 2.2.8 on 2020-06-05 06:06

import json
import os


from django.conf import settings
from django.db import migrations
from askanna_backend.core.utils import GoogleTokenGenerator, bx_decode


def forwards_func(apps, schema_editor):
    Package = apps.get_model("package", "Package")

    for package in Package.objects.filter(short_uuid=''):
        google_token = GoogleTokenGenerator()
        package.short_uuid = google_token.create_token(key="", uuid=package.uuid)
        print(package.short_uuid, package.uuid)
        package.save()


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("package", "0005_auto_20200519_2059"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
