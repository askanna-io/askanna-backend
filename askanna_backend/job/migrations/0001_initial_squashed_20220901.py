# Generated by Django 3.1.14 on 2022-09-01 13:14

import core.models
from django.conf import settings
import django.contrib.postgres.indexes
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import django_cryptography.fields
import django_extensions.db.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('package', '__first__'),
        ('project', '__first__'),
        ('users', '__first__'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChunkedArtifactPart',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('filename', models.CharField(max_length=500)),
                ('size', models.IntegerField(help_text='Size of this artifactchunk')),
                ('file_no', models.IntegerField()),
                ('is_last', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Job Artifact Chunk',
                'verbose_name_plural': 'Job Artifacts Chunks',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ChunkedJobOutputPart',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('filename', models.CharField(max_length=500)),
                ('size', models.IntegerField(help_text='Size of this resultchunk')),
                ('file_no', models.IntegerField()),
                ('is_last', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ChunkedRunResultPart',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('filename', models.CharField(max_length=500)),
                ('size', models.IntegerField(help_text='Size of this runresult')),
                ('file_no', models.IntegerField()),
                ('is_last', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='JobArtifact',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('size', models.PositiveIntegerField(default=0, editable=False)),
                ('count_dir', models.PositiveIntegerField(default=0, editable=False)),
                ('count_files', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'verbose_name': 'Job Artifact',
                'verbose_name_plural': 'Job Artifacts',
                'ordering': ['-created'],
            },
            bases=(core.models.ArtifactModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='JobDef',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='name')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('environment_image', models.CharField(blank=True, editable=False, max_length=2048, null=True)),
                ('timezone', models.CharField(default='UTC', max_length=256)),
            ],
            options={
                'verbose_name': 'Job Definition',
                'verbose_name_plural': 'Job Definitions',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='JobOutput',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('jobdef', models.UUIDField(blank=True, editable=False, null=True)),
                ('exit_code', models.IntegerField(default=0)),
                ('stdout', models.JSONField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Job Output',
                'verbose_name_plural': 'Job Outputs',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='JobPayload',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('size', models.PositiveIntegerField(default=0, editable=False)),
                ('lines', models.PositiveIntegerField(default=0, editable=False)),
            ],
            options={
                'verbose_name': 'Job Payload',
                'verbose_name_plural': 'Job Payloads',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='JobRun',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='name')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('jobid', models.CharField(blank=True, help_text='The job-id of the Celery run', max_length=120, null=True)),
                ('status', models.CharField(choices=[('SUBMITTED', 'SUBMITTED'), ('PENDING', 'PENDING'), ('IN_PROGRESS', 'IN_PROGRESS'), ('COMPLETED', 'COMPLETED'), ('FAILED', 'FAILED')], max_length=20)),
                ('trigger', models.CharField(blank=True, default='API', max_length=20, null=True)),
                ('started', models.DateTimeField(editable=False, null=True)),
                ('finished', models.DateTimeField(editable=False, null=True)),
                ('duration', models.PositiveIntegerField(blank=True, editable=False, help_text='Duration of the run in seconds', null=True)),
                ('environment_name', models.CharField(default='', max_length=256)),
                ('timezone', models.CharField(default='UTC', max_length=256)),
            ],
            options={
                'verbose_name': 'Job Run',
                'verbose_name_plural': 'Job Runs',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='JobVariable',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('name', models.CharField(max_length=128)),
                ('value', django_cryptography.fields.encrypt(models.TextField(blank=True, default=None, null=True))),
                ('is_masked', models.BooleanField(default=False)),
            ],
            options={
                'verbose_name': 'Job Variable',
                'verbose_name_plural': 'Job Variables',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='RunImage',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='name')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('tag', models.CharField(blank=True, editable=False, max_length=128, null=True)),
                ('digest', models.CharField(blank=True, editable=False, max_length=256, null=True)),
                ('cached_image', models.CharField(blank=True, editable=False, max_length=256, null=True)),
            ],
            options={
                'verbose_name': 'Run image',
                'verbose_name_plural': 'Run images',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='RunMetrics',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('count', models.PositiveIntegerField(default=0, editable=False, help_text='Count of metrics')),
                ('size', models.PositiveIntegerField(default=0, editable=False, help_text='File size of metrics JSON')),
                ('metric_names', models.JSONField(blank=True, default=None, editable=False, help_text='Unique metric names and data type for metric', null=True)),
                ('label_names', models.JSONField(blank=True, default=None, editable=False, help_text='Unique metric label names and data type for metric label', null=True)),
            ],
            options={
                'verbose_name': 'Run Metric',
                'verbose_name_plural': 'Run Metrics',
                'ordering': ['-created'],
            },
            bases=(core.models.ArtifactModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name='RunMetricsRow',
            fields=[
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('project_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('job_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('run_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('metric', models.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are metrics, but we limit to one')),
                ('label', models.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are labels')),
                ('created', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Run Metrics Row',
                'verbose_name_plural': 'Run Metrics Rows',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='RunResult',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True, verbose_name='description')),
                ('name', models.CharField(blank=True, max_length=255, null=True, verbose_name='name')),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('job', models.UUIDField(blank=True, editable=False, null=True)),
                ('mime_type', models.CharField(blank=True, help_text='Storing the mime-type of the output file', max_length=100, null=True)),
                ('size', models.PositiveIntegerField(default=0, editable=False, help_text='Size of the result stored')),
            ],
            options={
                'verbose_name': 'Run result',
                'verbose_name_plural': 'Run results',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='RunVariableRow',
            fields=[
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('project_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('job_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('run_suuid', models.CharField(db_index=True, editable=False, max_length=32)),
                ('variable', models.JSONField(default=None, editable=False, help_text='JSON field to store a variable')),
                ('is_masked', models.BooleanField(default=False)),
                ('label', models.JSONField(default=None, editable=False, help_text='JSON field as list with multiple objects which are labels')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'Run Variables Row',
                'verbose_name_plural': 'Run Variables Rows',
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ScheduledJob',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('short_uuid', models.CharField(blank=True, max_length=32, unique=True)),
                ('raw_definition', models.CharField(max_length=128)),
                ('cron_definition', models.CharField(max_length=128)),
                ('cron_timezone', models.CharField(max_length=64)),
                ('last_run', models.DateTimeField(help_text='The last run of this scheduled job', null=True)),
                ('next_run', models.DateTimeField(help_text='We store the datetime with timzone in UTC of the next run to be queried on', null=True)),
                ('job', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='job.jobdef')),
                ('member', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.membership')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RunVariables',
            fields=[
                ('created', django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name='created')),
                ('modified', django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name='modified')),
                ('deleted', models.DateTimeField(blank=True, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('count', models.PositiveIntegerField(default=0, editable=False, help_text='Count of variables')),
                ('size', models.PositiveIntegerField(default=0, editable=False, help_text='File size of variables JSON')),
                ('variable_names', models.JSONField(blank=True, default=None, editable=False, help_text='Unique variable names and data type for variable', null=True)),
                ('label_names', models.JSONField(blank=True, default=None, editable=False, help_text='Unique variable label names and data type for variable label', null=True)),
                ('jobrun', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='runvariables', to='job.jobrun')),
            ],
            options={
                'verbose_name': 'Run Variable',
                'verbose_name_plural': 'Run Variables',
                'ordering': ['-created'],
            },
            bases=(core.models.ArtifactModelMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name='runvariablerow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['variable'], name='runvariable_variable_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='runvariablerow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['label'], name='runvariable_label_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddField(
            model_name='runresult',
            name='run',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='result', to='job.jobrun'),
        ),
        migrations.AddIndex(
            model_name='runmetricsrow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['metric'], name='runmetric_metric_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddIndex(
            model_name='runmetricsrow',
            index=django.contrib.postgres.indexes.GinIndex(fields=['label'], name='runmetric_label_json_idx', opclasses=['jsonb_path_ops']),
        ),
        migrations.AddField(
            model_name='runmetrics',
            name='jobrun',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='metrics', to='job.jobrun'),
        ),
        migrations.AddField(
            model_name='jobvariable',
            name='project',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='variable', to='project.project'),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='jobdef',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='job.jobdef'),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='users.membership'),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='package',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='package.package'),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='payload',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.jobpayload'),
        ),
        migrations.AddField(
            model_name='jobrun',
            name='run_image',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='job.runimage'),
        ),
        migrations.AddField(
            model_name='jobpayload',
            name='jobdef',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payload', to='job.jobdef'),
        ),
        migrations.AddField(
            model_name='jobpayload',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='joboutput',
            name='jobrun',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='output', to='job.jobrun'),
        ),
        migrations.AddField(
            model_name='jobdef',
            name='project',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='project.project'),
        ),
        migrations.AddField(
            model_name='jobartifact',
            name='jobrun',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='artifact', to='job.jobrun'),
        ),
        migrations.AddField(
            model_name='chunkedrunresultpart',
            name='runresult',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.runresult'),
        ),
        migrations.AddField(
            model_name='chunkedjoboutputpart',
            name='joboutput',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.joboutput'),
        ),
        migrations.AddField(
            model_name='chunkedartifactpart',
            name='artifact',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='job.jobartifact'),
        ),
    ]