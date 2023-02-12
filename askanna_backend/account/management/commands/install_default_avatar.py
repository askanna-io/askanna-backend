from account.models import User, UserProfile
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Install default avatars for accounts who for some reason don't have an avatar yet"

    def handle(self, *args, **options):
        for userprofile in UserProfile.objects.all():
            try:
                userprofile.read
            except FileNotFoundError:
                userprofile.install_default_avatar()

        for userprofile in User.objects.all():
            try:
                userprofile.read
            except FileNotFoundError:
                userprofile.install_default_avatar()
