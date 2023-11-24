from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from storage.models import File
from storage.signals import file_complete


@receiver(post_save, sender=File)
def check_set_file_completed_at(sender, instance, created, update_fields, **kwargs):
    """
    Send file_complete signal when a file completed_at is set
    """
    if (created or (update_fields and "completed_at" in update_fields)) and instance.completed_at is not None:
        file_complete.send(sender=sender, instance=instance, created=created)


@receiver(pre_delete, sender=File)
def delete_file_and_empty_directories(instance, **kwargs):
    instance.delete_file_and_empty_directories()
