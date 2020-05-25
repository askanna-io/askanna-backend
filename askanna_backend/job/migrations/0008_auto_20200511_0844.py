# Generated by Django 2.2.8 on 2020-05-11 08:11

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('job', '0007_auto_20200409_0441'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='joboutput',
            options={'ordering': ['-created'], 'verbose_name': 'Job Output', 'verbose_name_plural': 'Job Outputs'},
        ),
        migrations.CreateModel(
            name='JobArtifact',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32)),
                ('size', models.PositiveIntegerField(default=0, editable=False)),
                ('jobdef', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artifact', to='job.JobDef')),
                ('jobrun', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artifact', to='job.JobRun')),
            ],
            options={
                'verbose_name': 'Job Artifact',
                'verbose_name_plural': 'Job Artifacts',
                'ordering': ['-created'],
            },
        ),
    ]
