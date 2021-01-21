import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from job.models import JobDef, JobPayload

# Default payloads to load for the standard jobs

payloads = {}


class Command(BaseCommand):
    help = "Install initial fixtures"

    def handle(self, *args, **options):
        for payload_id, value in payloads.items():
            pl = JobPayload.objects.get(pk=payload_id)

            store_path = [
                settings.PAYLOADS_ROOT,
                pl.storage_location,
            ]
            os.makedirs(os.path.join(*store_path), exist_ok=True)
            with open(os.path.join(*store_path, "payload.json"), "w") as f:
                f.write(json.dumps(value))
