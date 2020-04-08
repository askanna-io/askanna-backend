import json
import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from job.models import JobDef, JobPayload

# Default payloads to load for the standard jobs

payloads = {
    "9209f436-273a-44aa-b4cb-c92290ec330f": {"duration": 3},
    "e2e55775-c824-40c2-8e3d-8707aeb02289": {"duration": 600},
    "a52c6b98-3442-4530-b6fb-7091468873fa": {"name": "Test1"},
    "aceca258-fcd0-4479-9f49-d56c84fea185": {"name": "Test2"},
    "139860a0-f2a2-46a8-bcf3-b22f33c41d89": {"name": "Test3"},
    "2c1ccf99-27ba-4955-adc0-12dd7ed86d81": {"name": "Test4"},
    "578e6991-4367-41c6-806b-f9e2d873ed13": {"name": "Test5"},
    "99b61783-b2eb-4044-ab6b-63db43ffefee": {"name": "Test6"},
}


class Command(BaseCommand):
    help = 'Install initial fixtures'

    def handle(self, *args, **options):
        for payload_id, value in payloads.items():
            pl = JobPayload.objects.get(pk=payload_id)

            store_path = [
                settings.PAYLOADS_ROOT,
                pl.storage_location,
            ]
            os.makedirs(os.path.join(*store_path), exist_ok=True)
            with open(os.path.join(*store_path, "payload.json"), 'w') as f:
                f.write(json.dumps(value))