import os

from core.utils import get_files_and_directories_in_zip_file
from django.db import migrations
from job.models import JobArtifact


def update_artifact_counts(apps, schema_editor):
    artifacts = JobArtifact.objects.all()
    for artifact in artifacts:
        if os.path.exists(artifact.stored_path):
            zip_list = get_files_and_directories_in_zip_file(artifact.stored_path)
            artifact.count_dir = sum(map(lambda x: x["type"] == "directory", zip_list))
            artifact.count_files = sum(map(lambda x: x["type"] == "file", zip_list))
        else:
            print(f"Artifact file not found. JobArtifact UUID: {artifact.uuid}")

    JobArtifact.objects.bulk_update(artifacts, fields=["count_dir", "count_files"])


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0006_rename_jobrun_owner_and_remove_unused_fields"),
    ]

    operations = [
        migrations.RunPython(update_artifact_counts, reverse_func, elidable=True),
    ]
