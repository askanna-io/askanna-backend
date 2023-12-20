# Generated by Django 4.2.4 on 2023-09-13 14:39
import logging

import django.db.models.deletion
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import migrations, models

from account.models import User
from core.models import ObjectReference
from package.models import Package
from storage.models import File
from storage.utils.file import get_md5_from_file

logger = logging.getLogger(__name__)

package_root_path = settings.STORAGE_ROOT / "packages"


def move_package_files(apps, schema_editor):
    if not package_root_path.exists():
        logger.info(f"Package root directory '{package_root_path}' does not exist, nothing to do")
        return

    # First remove packages with finihsed_at=None, these are packages that were not finished uploading
    count_deleted = Package.objects.filter(archive_finished_at__isnull=True).delete()[0]
    if count_deleted > 0:
        logger.info(f"Deleted {count_deleted} packages that were not finished uploading")

    if Package.objects.count() > 0:
        user_anna = User.objects.get(username="anna")

        for package in Package.objects.all():
            package_path = package_root_path / str(package.project.uuid.hex) / str(package.uuid.hex)

            if package_path.exists():
                package_file = package_path / f"package_{package.uuid.hex}.zip"
                if package_file.exists():
                    # Historically we used the created_by field to indicate who uploaded the package and member was
                    # later introduced. If the member is set we use this value, else we switch to the created_by value.
                    #
                    # For even older packages where we did not store the created_by we use the project created_by. And
                    # if we also don't have a project created_by the package was automatically created by the system
                    # and for these cases we use the user 'anna' indicating that it was created by the system.
                    created_by = package.archive_created_by_member or package.archive_created_by_user
                    if created_by is None:
                        if package.project and package.project.created_by_user:
                            created_by = package.project.created_by_user
                        else:
                            created_by = user_anna

                    # Make sure we have an ObjectReference for package and created_by
                    ObjectReference.get_or_create(object=package)
                    ObjectReference.get_or_create(object=created_by)

                    content_file = ContentFile(package_file.read_bytes(), name=package.archive_filename)

                    file = File.objects.create(
                        name=package.archive_filename,
                        description=package.archive_description,
                        size=package.archive_size,
                        etag=get_md5_from_file(content_file),
                        content_type="application/zip",
                        file=content_file,
                        created_for=package,
                        created_by=created_by,
                        created_at=package.created_at,
                        modified_at=package.modified_at,
                        completed_at=package.archive_finished_at,
                    )

                    package.package_file = file
                    package.save(update_fields=["package_file"])

                    package_file.unlink()
                else:
                    raise Exception(f"Package file '{package_file}' does not exist, cannot move the package file.")
            else:
                if package.project.suuid == "7Lif-Rhcn-IRvS-Wv7J":
                    package.delete()
                else:
                    raise Exception(f"Package path '{package_path}' does not exist, cannot move the package file.")

    for project_directory in package_root_path.iterdir():
        if not project_directory.is_dir():
            continue

        for package_directory in project_directory.iterdir():
            try:
                package_directory.rmdir()
            except OSError:
                pass

        try:
            project_directory.rmdir()
        except OSError:
            pass

    try:
        package_root_path.rmdir()
    except OSError:
        logger.info(f"Package root directory '{package_root_path}' is not empty, not removing it")


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_objectreference_add_run_artifact"),
        ("storage", "0001_initial"),
        ("package", "0004_rename_package_and_delete_chunkedpackage"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="package_file",
            field=models.OneToOneField(
                null=True, on_delete=django.db.models.deletion.CASCADE, related_name="package_file", to="storage.file"
            ),
        ),
        migrations.RunPython(move_package_files, migrations.RunPython.noop, elidable=True),
    ]
