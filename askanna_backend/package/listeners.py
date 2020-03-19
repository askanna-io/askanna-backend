import os
from zipfile import ZipFile

from django.conf import settings
from django.dispatch import receiver

from package.signals import package_upload_finish


@receiver(package_upload_finish)
def handle_upload(sender, signal, postheaders, package, **kwargs):
    # print(sender)
    # print(signal)
    # print(postheaders)
    # print(kwargs)
    # print("DISPATCH UPLOAD PROCESSING TO WORKER")

    # extract from package_root to blob_root under the package uuid

    source_location = settings.PACKAGES_ROOT
    target_location = settings.BLOB_ROOT

    source_path = os.path.join(source_location, package.storage_location)
    target_path = os.path.join(target_location, str(package.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)
