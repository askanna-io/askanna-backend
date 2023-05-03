from pathlib import Path

from django.core.management.base import BaseCommand

from account.models.membership import UserProfile
from account.models.user import User


class Command(BaseCommand):
    help = "Install default avatars for accounts who for some reason don't have an avatar yet"

    def handle(self, *args, **options):
        for userprofile in UserProfile.objects.all():
            if not Path.exists(userprofile.avatar_path):
                userprofile.install_default_avatar()

        for user in User.objects.all():
            if not Path.exists(user.avatar_path):
                user.install_default_avatar()
