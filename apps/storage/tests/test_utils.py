from io import BytesIO

from django.core.files.base import ContentFile
from PIL import Image

from storage.utils import filename_for_resized_image, resize_image


def test_filename_for_resized_image():
    # Test with a filename that has an extension
    filename = "my_image.jpg"
    width = 100
    expected_result = "my_image_100x100.jpg"
    assert filename_for_resized_image(filename, width) == expected_result

    # Test with a filename that doesn't have an extension
    filename = "my_image"
    width = 200
    expected_result = "my_image_200x200"
    assert filename_for_resized_image(filename, width) == expected_result

    # Test with a filename that has multiple dots
    filename = "my.image.file.jpg"
    width = 300
    expected_result = "my.image.file_300x300.jpg"
    assert filename_for_resized_image(filename, width) == expected_result


def test_resize_image():
    # Create a test image
    with Image.new("RGB", (500, 500)) as image, BytesIO() as tmp_file:
        image.save(tmp_file, "png")
        image_file = ContentFile(tmp_file.getvalue(), name="my_image.png")

    # Resize the image
    width = 100
    resized_image_file = resize_image(image_file, width)

    # Check if the resized image has the correct dimensions
    resized_image = Image.open(resized_image_file)
    assert resized_image.size == (width, width)
