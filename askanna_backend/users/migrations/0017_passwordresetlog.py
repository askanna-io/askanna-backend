# Generated by Django 2.2.8 on 2020-12-02 12:30

from django.conf import settings
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0016_auto_20201125_1318'),
    ]

    operations = [
        migrations.CreateModel(
            name='PasswordResetLog',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('email', models.EmailField(max_length=254)),
                ('remote_ip', models.GenericIPAddressField(null=True, verbose_name='Remote IP')),
                ('remote_host', models.CharField(default=None, max_length=1024, null=True)),
                ('front_end_domain', models.CharField(default=None, max_length=1024, null=True)),
                ('meta', django.contrib.postgres.fields.jsonb.JSONField(default=None, null=True)),
                ('user', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
    ]
