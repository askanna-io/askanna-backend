from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('job', '0005_metrics_and_variables_deduplicate_for_historical_runs'),
    ]

    operations = [
        migrations.RenameField(
            model_name='jobrun',
            old_name='owner',
            new_name='created_by',
        ),
        migrations.AlterField(
            model_name='jobrun',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.RemoveField(
            model_name='joboutput',
            name='lines',
        ),
        migrations.RemoveField(
            model_name='joboutput',
            name='mime_type',
        ),
        migrations.RemoveField(
            model_name='joboutput',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='joboutput',
            name='size',
        ),
        migrations.RemoveField(
            model_name='runresult',
            name='lines',
        ),
        migrations.RemoveField(
            model_name='runresult',
            name='owner',
        ),
        migrations.AddField(
            model_name='jobartifact',
            name='count_dir',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AddField(
            model_name='jobartifact',
            name='count_files',
            field=models.PositiveIntegerField(default=0, editable=False),
        ),
        migrations.AlterModelOptions(
            name='chunkedartifactpart',
            options={'ordering': ['-created'], 'verbose_name': 'Job Artifact Chunk', 'verbose_name_plural': 'Job Artifacts Chunks'},
        ),
    ]
