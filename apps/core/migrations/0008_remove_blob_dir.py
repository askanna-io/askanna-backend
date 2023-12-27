import shutil

from django.conf import settings
from django.db import migrations


def remove_blob_dir(apps, schema_editor):
    blob_dir = settings.STORAGE_ROOT / "blob"

    if blob_dir.exists():
        shutil.rmtree(blob_dir)


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0005_move_package_files_to_storage"),
        ("run", "0004_move_run_artifact_files_to_storage"),
        ("core", "0007_alter_objectreference_account_membership_and_more"),
    ]

    operations = [
        migrations.RunPython(remove_blob_dir, migrations.RunPython.noop, elidable=True),
    ]
