import io
import logging

from django.db import migrations
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image

from account.models import User, Membership
from core.models import ObjectReference

logger = logging.getLogger(__name__)


avatar_root_path = settings.STORAGE_ROOT / "avatars"
default_image_path = settings.BASE_DIR / "resources/assets/src_assets_icons_ask-anna-default-gravatar.png"


def move_avatar_files_to_model(object: User | Membership, default_image):
    # Check if the object has an avatar
    avatar_path = avatar_root_path / object.uuid.hex
    if avatar_path.exists():
        avatar_file = avatar_path / f"avatar_{object.uuid.hex}.image"
        if avatar_file.exists():
            # Don't create a avatar for user/membership if the avatar image is the default image
            with Image.open(avatar_file) as avatar_image:
                if avatar_image != default_image:
                    with io.BytesIO() as tmp_file:
                        # Make sure we have an ObjectReference for the object
                        ObjectReference.get_or_create(object=object)

                        # All avatar images are stored as .image files (unknown type), convert them to .png
                        avatar_image.save(fp=tmp_file, format="png")

                        object.set_avatar(
                            ContentFile(
                                tmp_file.getvalue(),
                                name=f"avatar_{object.uuid.hex}.png",
                            )
                        )

        # Remove all files in avatar_path and remove the directory
        for file in avatar_path.iterdir():
            file.unlink()
        avatar_path.rmdir()


def move_avatar_files(apps, schema_editor):
    if not avatar_root_path.exists():
        logger.info(f"Avatar root directory '{avatar_root_path}' does not exist, nothing to do")
        return

    # Get list of directories and files in the avatar root directory
    avatar_directories = [directory for directory in avatar_root_path.iterdir() if directory.is_dir()]
    avatar_files = [file for file in avatar_root_path.iterdir() if file.is_file()]

    default_image = Image.open(default_image_path)

    for user in User.objects.all():
        move_avatar_files_to_model(user, default_image)

    for membership in Membership.objects.all():
        move_avatar_files_to_model(membership, default_image)

    default_image.close()

    for file in avatar_files:
        file.unlink(missing_ok=True)

    for directory in avatar_directories:
        if directory.exists():
            logger.info(f"Removing directory '{directory}' because it was not removed while moving the avatar files")
            for file in directory.iterdir():
                if file.is_file():
                    file.unlink()
            try:
                directory.rmdir()
            except OSError:
                logger.info(f"Directory '{directory}' is not empty, not removing it")

    try:
        avatar_root_path.rmdir()
    except OSError:
        logger.info(f"Avatar root directory '{avatar_root_path}' is not empty, not removing it")


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0002_alter_membership_job_title_delete_userprofile"),
        ("core", "0004_add_objectreference"),
        ("storage", "__first__"),
    ]

    operations = [
        migrations.RunPython(move_avatar_files, migrations.RunPython.noop),
    ]