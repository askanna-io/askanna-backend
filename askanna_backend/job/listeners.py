from django.db.models.signals import pre_delete
from django.dispatch import receiver
from job.models import JobPayload


@receiver(pre_delete, sender=JobPayload)
def delete_jobpayload(sender, instance, **kwargs):
    instance.prune()
