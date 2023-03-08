# Generated by Django 3.2.16 on 2022-11-07 08:25

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0005_rename_short_uuid_to_suuid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='suuid',
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name='SUUID'),
        ),
        migrations.AlterField(
            model_name='project',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='UUID'),
        ),
        migrations.AlterField(
            model_name='projectvariable',
            name='suuid',
            field=models.CharField(editable=False, max_length=32, unique=True, verbose_name='SUUID'),
        ),
        migrations.AlterField(
            model_name='projectvariable',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, verbose_name='UUID'),
        ),
    ]