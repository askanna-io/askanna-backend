from io import BytesIO

from django.core.files.base import ContentFile, File
from PIL import Image, ImageOps


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
