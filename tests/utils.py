import tempfile

from django.core.files.base import ContentFile
from PIL import Image


def get_avatar_file(suffix=".jpg"):
    image = Image.new("RGB", (100, 100))

    tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
    image.save(tmp_file)
    tmp_file.seek(0)

    return tmp_file


def get_avatar_content_file() -> ContentFile:
    return ContentFile(get_avatar_file(suffix=".png").read(), name="test_avatar.png")
