# Generated by Django 3.1.14 on 2022-09-01 12:52

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('project', '__first__'),
        ('users', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='Package',
            fields=[
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('size', models.IntegerField(help_text='Size of this package in bytes')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('project', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='packages', related_query_name='package', to='project.project')),
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True,  verbose_name='created')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('original_filename', models.CharField(default='', max_length=1000)),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.membership')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='name')),
                ('finished', models.DateTimeField(blank=True, db_index=True, help_text='Time when upload of this package was finished', null=True, verbose_name='Finished upload')),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ChunkedPackagePart',
            fields=[
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('filename', models.CharField(max_length=500)),
                ('size', models.IntegerField(help_text='Size of this chunk of the package')),
                ('file_no', models.IntegerField()),
                ('is_last', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('deleted_at', models.DateTimeField(null=True)),
                ('package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='package.package')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]
