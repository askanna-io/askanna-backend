from django.core.management.base import BaseCommand
from users.models import UserProfile


class Command(BaseCommand):
    help = (
        "Install default avatars for users who for some reason don't have an avatar yet"
    )

    def handle(self, *args, **options):
        for userprofile in UserProfile.objects.all():
            try:
                userprofile.read
            except FileNotFoundError as e:
                print(e)
                userprofile.install_default_avatar()
