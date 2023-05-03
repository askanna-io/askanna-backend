from django.core.management.base import BaseCommand

from core.models import Setting


class Command(BaseCommand):
    help = "Install default must have settings allowing admins to change"

    def handle(self, *args, **options):
        must_have_settings = {
            "DOCKER_AUTO_REMOVE_TTL": 1,  # in hours, can be fractional
            "OBJECT_REMOVAL_TTL_HOURS": 720,  # removal after 30 days
        }
        for setting_name, default_value in must_have_settings.items():
            setting, created = Setting.objects.get_or_create(name=setting_name)
            if created:
                setting.value = default_value
                setting.save(update_fields=["value"])
