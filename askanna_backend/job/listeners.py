import os
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.dispatch import receiver

from yaml import load, dump

try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

from job.signals import artifact_upload_finish


@receiver(artifact_upload_finish)
def handle_upload(sender, signal, postheaders, obj, **kwargs):
    """
    After saving the artifact, we extract the contents of the artifact to
    BLOB_ROOT, which is served on the CDN to allow us to retrieve the individual
    files one by one.
    """
    source_location = settings.ARTIFACTS_ROOT
    target_location = settings.BLOB_ROOT

    source_path = os.path.join(source_location, obj.storage_location, obj.filename)
    target_path = os.path.join(target_location, str(obj.uuid))

    with ZipFile(source_path) as zippackage:
        zippackage.extractall(path=target_path)
