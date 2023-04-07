# Generated by Django 3.2.16 on 2022-11-07 08:25

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("job", "0009_rename_short_uuid_to_suuid"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobdef",
            name="suuid",
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name="SUUID"),
        ),
        migrations.AlterField(
            model_name="jobdef",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="UUID"
            ),
        ),
        migrations.AlterField(
            model_name="jobpayload",
            name="suuid",
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name="SUUID"),
        ),
        migrations.AlterField(
            model_name="jobpayload",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="UUID"
            ),
        ),
        migrations.AlterField(
            model_name="runimage",
            name="suuid",
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name="SUUID"),
        ),
        migrations.AlterField(
            model_name="runimage",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="UUID"
            ),
        ),
        migrations.AlterField(
            model_name="scheduledjob",
            name="suuid",
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name="SUUID"),
        ),
        migrations.AlterField(
            model_name="scheduledjob",
            name="uuid",
            field=models.UUIDField(
                default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name="UUID"
            ),
        ),
    ]
