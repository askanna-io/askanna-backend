import json
import os
import shutil


from django.conf import settings
from django.db import migrations


def forwards_func(apps, schema_editor):
    Package = apps.get_model("package", "Package")

    for package in Package.objects.all():
        package.original_filename = package.storage_location
        package.save()
        # move package to the new location
        # create directories
        folder = os.path.join(
            settings.PACKAGES_ROOT, package.project.uuid.hex, package.uuid.hex
        )
        os.makedirs(folder, exist_ok=True)

        src = os.path.join(settings.PACKAGES_ROOT, package.storage_location)
        dst = os.path.join(folder, "package_{}.zip".format(package.uuid.hex))
        # copy the file to the new location, we try this, because not always the upload was correct in the past
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            print(type(e), e)

    # now remove the packages
    # we do this in a separate loop to avoid removing overlapping filename from previous operation
    for package in Package.objects.all():
        src = os.path.join(settings.PACKAGES_ROOT, package.storage_location)
        if not package.storage_location:
            # skip empty filenames
            continue
        try:
            os.remove(src)
        except Exception as e:
            print(type(e), e)


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("package", "0010_package_original_filename"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
