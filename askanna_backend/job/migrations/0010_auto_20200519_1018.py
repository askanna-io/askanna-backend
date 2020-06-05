# Generated by Django 2.2.8 on 2020-05-19 10:18

import json
import os
from django.conf import settings
from django.db import migrations

def forwards_func(apps, schema_editor):
    JobPayload = apps.get_model("job", "JobPayload")

    for job in JobPayload.objects.all():
        payload = ""

        storage_location = os.path.join(job.jobdef.project.uuid.hex, job.short_uuid)
        store_path = [settings.PAYLOADS_ROOT, storage_location, "payload.json"]

        try:
            with open(os.path.join(*store_path), "r") as f:
                payload = f.read()
        except Exception as e:
            print(e)

        size = len(payload)
        lines = 0
        try:
            lines = len(json.dumps(json.loads(payload), indent=1).splitlines())
        except:
            pass
        job.size = size
        job.lines = lines
        job.save(update_fields=['size', 'lines'])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0009_auto_20200519_1013'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]