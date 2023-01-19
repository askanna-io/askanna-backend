# Generated by Django 3.2.16 on 2022-12-14 12:49

import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.manager
from users.models import User


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_uuid_and_suuid_field_config"),
    ]

    def forwards_func(apps, schema_editor):
        for user in User.objects.filter(name__isnull=True):
            if not user.name:
                user.name = user.email.split("@")[0]
                user.save()

    def reverse_func(apps, schema_editor):
        pass

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("memberships", django.db.models.manager.Manager()),
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.RemoveField(
            model_name="invitation",
            name="front_end_url",
        ),
        migrations.RemoveField(
            model_name="user",
            name="first_name",
        ),
        migrations.RemoveField(
            model_name="user",
            name="front_end_domain",
        ),
        migrations.RemoveField(
            model_name="user",
            name="last_name",
        ),
        migrations.AlterField(
            model_name="membership",
            name="name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Name"),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(max_length=254, verbose_name="Email address"),
        ),
        migrations.AlterField(
            model_name="user",
            name="job_title",
            field=models.CharField(blank=True, default="", max_length=255, verbose_name="Job title"),
        ),
        migrations.AlterField(
            model_name="user",
            name="name",
            field=models.CharField(max_length=255, verbose_name="Name of User"),
        ),
    ]
