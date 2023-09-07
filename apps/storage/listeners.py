from pathlib import Path

from django.conf import settings
from django.db.models.signals import pre_delete
from django.dispatch import receiver

from storage.models import File


@receiver(pre_delete, sender=File)
def delete_file_and_empty_directories(instance, **kwargs):
    directories = Path(instance.file.path).parents if settings.ASKANNA_FILESTORAGE == "filesystem" else None

    instance.file.delete(save=False)

    if directories:
        for directory in directories:
            if (
                directory.exists()
                and directory.is_dir()
                and not any(directory.iterdir())  # Only delete empty directories
                and directory != settings.STORAGE_ROOT  # Don't delete the storage root directory
            ):
                directory.rmdir()
            else:
                break
