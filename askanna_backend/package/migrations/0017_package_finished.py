# Generated by Django 2.2.24 on 2021-09-22 00:18
import datetime
import os

from django.conf import settings
from django.db import migrations, models
import pytz


def forwards_func(apps, schema_editor):
    Package = apps.get_model("package", "Package")

    def storage_location(package):
        return os.path.join(
            package.project.uuid.hex,
            package.uuid.hex,
        )

    def stored_path(package):
        return os.path.join(
            settings.PACKAGES_ROOT, storage_location(package), "package_{}.zip".format(package.uuid.hex)
        )

    for package in Package.objects.all():
        try:
            timestamp = os.path.getmtime(stored_path(package))
        except OSError:
            pass
        else:
            package.finished = datetime.datetime.fromtimestamp(timestamp, tz=pytz.UTC)
            package.save(update_fields=["finished"])


def reverse_func(apps, schema_editor):
    ...


class Migration(migrations.Migration):

    dependencies = [
        ("package", "0016_fill_in_member"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="finished",
            field=models.DateTimeField(
                blank=True,
                db_index=True,
                help_text="Time when upload of this package was finished",
                null=True,
                verbose_name="Finished upload",
            ),
        ),
        migrations.RunPython(forwards_func, reverse_func),
    ]