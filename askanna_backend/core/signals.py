from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework.authtoken.models import Token


@receiver(post_save, sender=get_user_model())
def create_user_api_key_signal(sender, instance, created, **kwargs):
    """
    Create a Django DRF API key, when a new user gets created.
    """

    if created:
        Token.objects.create(user=instance)
