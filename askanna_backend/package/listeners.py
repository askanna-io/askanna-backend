import os
from zipfile import ZipFile

from django.conf import settings
from django.dispatch import receiver

from package.signals import package_upload_finish


@receiver(package_upload_finish)
def handle_upload(sender, signal, postheaders, obj, **kwargs):
    # extract from package_root to blob_root under the package uuid
    # this is for the fileview
    source_location = settings.PACKAGES_ROOT
    target_location = settings.BLOB_ROOT

    source_path = os.path.join(source_location, obj.storage_location)
    target_path = os.path.join(target_location, str(obj.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)
