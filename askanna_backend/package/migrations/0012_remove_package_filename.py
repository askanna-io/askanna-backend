# Generated by Django 2.2.8 on 2020-12-09 12:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("package", "0011_migrate_storage_location_to_original_filename"),
    ]

    operations = [
        migrations.RemoveField(model_name="package", name="filename",),
        migrations.RemoveField(model_name="package", name="storage_location",),
    ]