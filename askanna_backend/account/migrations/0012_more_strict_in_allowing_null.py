# Generated by Django 4.1.7 on 2023-03-30 12:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0011_change_meta_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="passwordresetlog",
            name="front_end_domain",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
        migrations.AlterField(
            model_name="passwordresetlog",
            name="remote_host",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
    ]