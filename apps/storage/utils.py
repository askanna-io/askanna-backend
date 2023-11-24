import hashlib
import json
import mimetypes
from io import BytesIO
from os import PathLike

import magic
from django.conf import settings
from django.core.files.base import ContentFile, File
from PIL import Image, ImageOps


def is_json_file(file: File | PathLike | bytes) -> bool:
    """
    Determine whether we are dealing with a JSON file
    returns True/False
    """

    try:
        if hasattr(file, "read"):
            file.seek(0)
            json.load(file)
        else:
            with file.open() as f:
                json.load(f)

    except json.decoder.JSONDecodeError:
        return False

    return True


def get_content_type_from_file(file: File | PathLike | str | bytes, default: str = None) -> str:
    """
    Get the content type from a file.

    If the file has a content_type attribute, use that. Otherwise, use libmagic to determine the content type. If that
    fails, use guess_type from Python's builtin mimetypes module and as a final fallback use the default
    content type from the settings.

    If the content type is text/plain, we do an additional check to see if it is a JSON file. If so, we return
    "application/json".

    Args:
        file_object: the file to get the content type from

    Returns:
        content_type (str): the content type of the file
    """
    detected_content_type = None
    default_content_type = default or settings.ASKANNA_DEFAULT_CONTENT_TYPE

    if hasattr(file, "content_type"):
        return file.content_type

    if hasattr(file, "read"):
        file.seek(0)
        detected_content_type = magic.from_buffer(file.read(2048), mime=True)
    else:
        detected_content_type = magic.from_file(file, mime=True)

    if not detected_content_type:
        detected_content_type = mimetypes.guess_type(file.name)[0] or default_content_type

    if detected_content_type and detected_content_type == "text/plain":
        if is_json_file(file):
            detected_content_type = "application/json"

    if hasattr(file, "seek"):
        file.seek(0)

    return detected_content_type


def get_md5_from_file(file) -> str:
    """
    Get the MD5 hash of a file.

    If the file is larger then FILE_MAX_MEMORY_SIZE and the file has a chunks method, use that to iterate over the
    file to get the file's MD5 hash. Otherwise, try to read the entire file into memory and hash it.

    Args:
        file: the file to get the md5 from

    Returns:
        md5 (str): The MD5 hash of the file
    """
    md5 = hashlib.md5(usedforsecurity=False)

    if hasattr(file, "seek"):
        file_opened = False
        file.seek(0)
    else:
        file_opened = True
        file = file.open("rb")

    if hasattr(file, "chunks") and file.size > settings.FILE_MAX_MEMORY_SIZE:
        for chunk in file.chunks():
            md5.update(chunk)
    else:
        md5.update(file.read())

    if file_opened is True:
        file.close()
    elif hasattr(file, "seek"):
        file.seek(0)

    return md5.hexdigest()


def filename_for_resized_image(filename: str, width: int) -> str:
    """
    Generate a filename for a resized image. The filename will be the same as the original filename, but with the width
    appended to the filename, just before the extension.

    Args:
        filename (str): filename of the original image
        width (int): the width of the square to resize the image to

    Returns:
        str: the filename for the resized image
    """
    filename = filename.split(".")

    if len(filename) == 1:
        filename = f"{filename[0]}_{width}x{width}"
    else:
        filename[-2] = f"{filename[-2]}_{width}x{width}"
        filename = ".".join(filename)

    return filename


def resize_image(image_object: File, width: int) -> ContentFile:
    """
    Resize an image to a square of the given width.

    Args:
        image_object (File): a Django File object containing an image file
        width (int): the width of the square to resize the image to

    Returns:
        ContentFile: a Django ContentFile object containing the resized image
    """
    filename = filename_for_resized_image(image_object.name, width)

    with image_object as image_file, Image.open(image_file) as image, BytesIO() as tmp_file:
        ImageOps.fit(
            ImageOps.exif_transpose(image),  # Make sure the image is rotated correctly
            (width, width),
        ).save(tmp_file, format=image.format)

        return ContentFile(tmp_file.getvalue(), name=filename)