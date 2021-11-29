# Generated by Django 2.2.24 on 2021-11-28 23:04

import core.fields
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

    replaces = [
        ("job", "0001_initial"),
        ("job", "0002_auto_20200402_0652"),
        ("job", "0003_auto_20200402_0801"),
        ("job", "0004_auto_20200402_1203"),
        ("job", "0005_remove_jobpayload_storage_location"),
        ("job", "0006_jobdef_default_payload"),
        ("job", "0007_auto_20200409_0441"),
        ("job", "0008_auto_20200511_0844"),
        ("job", "0009_auto_20200519_1013"),
        ("job", "0010_auto_20200519_1018"),
        ("job", "0011_chunkedartifactpart"),
        ("job", "0012_remove_jobartifact_jobdef"),
        ("job", "0013_jobvariable"),
        ("job", "0014_jobrun_package"),
        ("job", "0015_remove_joboutput_return_payload"),
        ("job", "0016_chunkedjoboutputpart"),
        ("job", "0017_auto_20200803_1316"),
        ("job", "0018_auto_20201028_2111"),
        ("job", "0019_jobvariable_is_masked"),
        ("job", "0020_auto_20201119_1029"),
        ("job", "0021_auto_20201201_1545"),
        ("job", "0022_auto_20210105_0922"),
        ("job", "0023_auto_20210211_1505"),
        ("job", "0024_auto_20210216_0904"),
        ("job", "0025_auto_20210303_1621"),
        ("job", "0026_auto_20210326_1454"),
        ("job", "0027_auto_20210408_0703"),
        ("job", "0028_auto_20210411_2025"),
        ("job", "0029_auto_20210414_0758"),
        ("job", "0030_auto_20210414_0951"),
        ("job", "0031_custom_images"),
        ("job", "0032_auto_20210707_1428"),
        ("job", "0033_jobvariable_value"),
        ("job", "0034_remove_jobvariable_old_value"),
        ("job", "0032_custom_images_migrate_result"),
        ("job", "0033_auto_20210726_1205"),
        ("job", "0034_fix_default_askanna_image"),
        ("job", "0035_merge_20210916_2355"),
    ]

    initial = True

    dependencies = [
        ("project", "__first__"),
        ("project", "0001_initial"),
        ("users", "0019_auto_20201222_1508"),
        ("package", "0005_auto_20200519_2059"),
    ]

    operations = [
        migrations.CreateModel(
            name="JobDef",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32)),
                ("name", models.CharField(max_length=50)),
                (
                    "project",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="project.Project"
                    ),
                ),
            ],
            options={
                "verbose_name": "Job Definition",
                "verbose_name_plural": "Job Definitions",
            },
        ),
        migrations.CreateModel(
            name="JobRun",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32)),
                ("payload", models.UUIDField(blank=True, editable=False, null=True)),
                ("jobid", models.CharField(blank=True, max_length=120, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("SUBMITTED", "SUBMITTED"),
                            ("COMPLETED", "COMPLETED"),
                            ("PENDING", "PENDING"),
                            ("PAUSED", "PAUSED"),
                            ("IN_PROGRESS", "IN_PROGRESS"),
                            ("FAILED", "FAILED"),
                            ("SUCCESS", "SUCCESS"),
                        ],
                        max_length=20,
                    ),
                ),
                ("owner", models.CharField(blank=True, max_length=100, null=True)),
                ("jobdef", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="job.JobDef")),
            ],
            options={
                "verbose_name": "Job Run",
                "verbose_name_plural": "Job Runs",
            },
        ),
        migrations.CreateModel(
            name="JobOutput",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32)),
                ("jobdef", models.UUIDField(blank=True, editable=False, null=True)),
                ("exit_code", models.IntegerField(default=0)),
                ("stdout", core.fields.JSONField(blank=True, null=True)),
                ("owner", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "jobrun",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.DO_NOTHING, related_name="output", to="job.JobRun"
                    ),
                ),
            ],
            options={
                "verbose_name": "Job Output",
                "verbose_name_plural": "Job Outputs",
            },
        ),
        migrations.CreateModel(
            name="JobPayload",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32)),
                (
                    "owner",
                    models.ForeignKey(
                        null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "jobdef",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="payload", to="job.JobDef"
                    ),
                ),
            ],
            options={
                "verbose_name": "Job Payload",
                "verbose_name_plural": "Job Payloads",
            },
        ),
        migrations.AlterModelOptions(
            name="jobdef",
            options={
                "ordering": ["-created"],
                "verbose_name": "Job Definition",
                "verbose_name_plural": "Job Definitions",
            },
        ),
        migrations.AlterModelOptions(
            name="jobpayload",
            options={"ordering": ["-created"], "verbose_name": "Job Payload", "verbose_name_plural": "Job Payloads"},
        ),
        migrations.AlterModelOptions(
            name="jobrun",
            options={"ordering": ["-created"], "verbose_name": "Job Run", "verbose_name_plural": "Job Runs"},
        ),
        migrations.AlterField(
            model_name="jobrun",
            name="owner",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AlterField(
            model_name="jobrun",
            name="payload",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="job.JobPayload"),
        ),
        migrations.AlterModelOptions(
            name="joboutput",
            options={"ordering": ["-created"], "verbose_name": "Job Output", "verbose_name_plural": "Job Outputs"},
        ),
        migrations.CreateModel(
            name="JobArtifact",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32)),
                ("size", models.PositiveIntegerField(default=0, editable=False)),
                (
                    "jobrun",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="artifact", to="job.JobRun"
                    ),
                ),
            ],
            options={
                "verbose_name": "Job Artifact",
                "verbose_name_plural": "Job Artifacts",
                "ordering": ["-created"],
            },
        ),
        migrations.AddField(
            model_name="jobpayload",
            name="lines",
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="jobpayload",
            name="size",
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="package",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="package.Package"),
        ),
        migrations.AlterField(
            model_name="jobartifact",
            name="short_uuid",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name="jobdef",
            name="short_uuid",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name="joboutput",
            name="short_uuid",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name="jobpayload",
            name="short_uuid",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name="jobrun",
            name="short_uuid",
            field=models.CharField(blank=True, max_length=32, unique=True),
        ),
        migrations.CreateModel(
            name="JobVariable",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("name", models.CharField(max_length=128)),
                ("value", django_cryptography.fields.encrypt(models.TextField(blank=True, default=None, null=True))),
                (
                    "project",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="variable", to="project.Project"
                    ),
                ),
                ("is_masked", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Job Variable",
                "verbose_name_plural": "Job Variables",
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="ChunkedArtifactPart",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("filename", models.CharField(max_length=500)),
                ("size", models.IntegerField(help_text="Size of this artifactchunk")),
                ("file_no", models.IntegerField()),
                ("is_last", models.BooleanField(default=False)),
                (
                    "artifact",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="job.JobArtifact"
                    ),
                ),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="ChunkedJobOutputPart",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("filename", models.CharField(max_length=500)),
                ("size", models.IntegerField(help_text="Size of this resultchunk")),
                ("file_no", models.IntegerField()),
                ("is_last", models.BooleanField(default=False)),
                (
                    "joboutput",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="job.JobOutput"
                    ),
                ),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.AlterField(
            model_name="jobdef",
            name="project",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="project.Project"
            ),
        ),
        migrations.AlterField(
            model_name="joboutput",
            name="jobrun",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="output", to="job.JobRun"
            ),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="member",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="users.Membership"),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="metric_keys",
            field=core.fields.ArrayField(
                base_field=models.CharField(max_length=8192), blank=True, default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="metric_labels",
            field=core.fields.ArrayField(
                base_field=models.CharField(max_length=4096), blank=True, default=list, size=None
            ),
        ),
        migrations.CreateModel(
            name="RunMetrics",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("count", models.PositiveIntegerField(default=0, editable=False)),
                ("size", models.PositiveIntegerField(default=0, editable=False)),
                (
                    "jobrun",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="metrics", to="job.JobRun"
                    ),
                ),
            ],
            options={
                "verbose_name": "Run Metrics",
                "verbose_name_plural": "Run Metrics",
                "ordering": ["-created"],
            },
            bases=(core.models.ArtifactModelMixin, models.Model),
        ),
        migrations.CreateModel(
            name="RunMetricsRow",
            fields=[
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("project_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                ("job_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                ("run_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                (
                    "metric",
                    core.fields.JSONField(
                        help_text="JSON field as list with multiple objects which are metrics, but we limit to one for db scanning only"
                    ),
                ),
                (
                    "label",
                    core.fields.JSONField(help_text="JSON field as list with multiple objects which are labels"),
                ),
                ("created", models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.AddIndex(
            model_name="runmetricsrow",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["metric"], name="metric_json_index", opclasses=["jsonb_path_ops"]
            ),
        ),
        migrations.AddIndex(
            model_name="runmetricsrow",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["label"], name="label_json_index", opclasses=["jsonb_path_ops"]
            ),
        ),
        migrations.AlterField(
            model_name="runmetricsrow",
            name="metric",
            field=core.fields.JSONField(
                help_text="JSON field as list with multiple objects which are metrics, but we limit to one"
            ),
        ),
        migrations.AddField(
            model_name="joboutput",
            name="lines",
            field=models.PositiveIntegerField(default=0, editable=False, help_text="Number of lines in the result"),
        ),
        migrations.AddField(
            model_name="joboutput",
            name="mime_type",
            field=models.CharField(
                blank=True, help_text="Storing the mime-type of the output file", max_length=100, null=True
            ),
        ),
        migrations.AddField(
            model_name="joboutput",
            name="size",
            field=models.PositiveIntegerField(default=0, editable=False, help_text="Size of the result stored"),
        ),
        migrations.CreateModel(
            name="RunVariableRow",
            fields=[
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("project_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                ("job_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                ("run_suuid", models.CharField(db_index=True, editable=False, max_length=32)),
                ("created", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("is_masked", models.BooleanField(default=False)),
                ("variable", core.fields.JSONField(help_text="JSON field to store a variable")),
                (
                    "label",
                    core.fields.JSONField(help_text="JSON field as list with multiple objects which are labels"),
                ),
            ],
            options={
                "verbose_name": "Tracked Run Variable",
                "verbose_name_plural": "Tracked Run Variables",
                "ordering": ["-created"],
            },
        ),
        migrations.AddField(
            model_name="jobrun",
            name="variable_keys",
            field=core.fields.ArrayField(
                base_field=models.CharField(max_length=8192), blank=True, default=list, size=None
            ),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="variable_labels",
            field=core.fields.ArrayField(
                base_field=models.CharField(max_length=4096), blank=True, default=list, size=None
            ),
        ),
        migrations.CreateModel(
            name="RunVariables",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("count", models.PositiveIntegerField(default=0, editable=False)),
                ("size", models.PositiveIntegerField(default=0, editable=False)),
                (
                    "jobrun",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="runvariables", to="job.JobRun"
                    ),
                ),
            ],
            options={
                "verbose_name": "Run Variables",
                "verbose_name_plural": "Run Variables",
                "ordering": ["-created"],
            },
            bases=(core.models.ArtifactModelMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name="runvariablerow",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["label"], name="runvariable_var_json_idx", opclasses=["jsonb_path_ops"]
            ),
        ),
        migrations.AddIndex(
            model_name="runvariablerow",
            index=django.contrib.postgres.indexes.GinIndex(
                fields=["label"], name="runvariable_lbl_json_idx", opclasses=["jsonb_path_ops"]
            ),
        ),
        migrations.AlterModelOptions(
            name="runvariablerow",
            options={
                "ordering": ["-created"],
                "verbose_name": "Run variable row",
                "verbose_name_plural": "Run variable rows",
            },
        ),
        migrations.AddField(
            model_name="jobrun",
            name="trigger",
            field=models.CharField(blank=True, default="API", max_length=20, null=True),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="name"),
        ),
        migrations.AlterField(
            model_name="jobdef",
            name="name",
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name="name"),
        ),
        migrations.CreateModel(
            name="ScheduledJob",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("raw_definition", models.CharField(max_length=128)),
                ("cron_definition", models.CharField(max_length=128)),
                ("cron_timezone", models.CharField(max_length=64)),
                ("last_run", models.DateTimeField(help_text="The last run of this scheduled job", null=True)),
                (
                    "next_run",
                    models.DateTimeField(
                        help_text="We store the datetime with timzone in UTC of the next run to be queried on",
                        null=True,
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="schedules",
                        to="job.JobDef",
                    ),
                ),
                (
                    "member",
                    models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to="users.Membership"),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="RunImage",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                ("name", models.CharField(blank=True, max_length=255, null=True, verbose_name="name")),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("tag", models.CharField(blank=True, editable=False, max_length=128, null=True)),
                ("digest", models.CharField(blank=True, editable=False, max_length=256, null=True)),
                ("cached_image", models.CharField(blank=True, editable=False, max_length=256, null=True)),
            ],
            options={
                "verbose_name": "Run image",
                "verbose_name_plural": "Run images",
                "ordering": ["-created"],
            },
        ),
        migrations.AddField(
            model_name="jobdef",
            name="environment_image",
            field=models.CharField(blank=True, editable=False, max_length=2048, null=True),
        ),
        migrations.AddField(
            model_name="jobdef",
            name="timezone",
            field=models.CharField(default="UTC", max_length=256),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="duration",
            field=models.PositiveIntegerField(blank=True, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="environment_name",
            field=models.CharField(default="", max_length=256),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="finished",
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="started",
            field=models.DateTimeField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="jobrun",
            name="timezone",
            field=models.CharField(default="UTC", max_length=256),
        ),
        migrations.CreateModel(
            name="RunResult",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                ("description", models.TextField(blank=True, null=True, verbose_name="description")),
                ("name", models.CharField(blank=True, max_length=255, null=True, verbose_name="name")),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("job", models.UUIDField(blank=True, editable=False, null=True)),
                (
                    "mime_type",
                    models.CharField(
                        blank=True, help_text="Storing the mime-type of the output file", max_length=100, null=True
                    ),
                ),
                (
                    "size",
                    models.PositiveIntegerField(default=0, editable=False, help_text="Size of the result stored"),
                ),
                (
                    "lines",
                    models.PositiveIntegerField(default=0, editable=False, help_text="Number of lines in the result"),
                ),
                ("owner", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "run",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name="result", to="job.JobRun"
                    ),
                ),
            ],
            options={
                "verbose_name": "Run result",
                "verbose_name_plural": "Run results",
                "ordering": ["-created"],
            },
        ),
        migrations.CreateModel(
            name="ChunkedRunResultPart",
            fields=[
                (
                    "created",
                    django_extensions.db.fields.CreationDateTimeField(auto_now_add=True, verbose_name="created"),
                ),
                (
                    "modified",
                    django_extensions.db.fields.ModificationDateTimeField(auto_now=True, verbose_name="modified"),
                ),
                ("deleted", models.DateTimeField(blank=True, null=True)),
                (
                    "uuid",
                    models.UUIDField(
                        db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("short_uuid", models.CharField(blank=True, max_length=32, unique=True)),
                ("filename", models.CharField(max_length=500)),
                ("size", models.IntegerField(help_text="Size of this runresult")),
                ("file_no", models.IntegerField()),
                ("is_last", models.BooleanField(default=False)),
                (
                    "runresult",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="job.RunResult"
                    ),
                ),
            ],
            options={
                "ordering": ["-created"],
            },
        ),
        migrations.AddField(
            model_name="jobrun",
            name="run_image",
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to="job.RunImage"),
        ),
        migrations.AlterField(
            model_name="jobrun",
            name="status",
            field=models.CharField(
                choices=[
                    ("SUBMITTED", "SUBMITTED"),
                    ("PENDING", "PENDING"),
                    ("IN_PROGRESS", "IN_PROGRESS"),
                    ("COMPLETED", "COMPLETED"),
                    ("FAILED", "FAILED"),
                ],
                max_length=20,
            ),
        ),
    ]
