import csv
import json
import tempfile
import zipfile
from pathlib import Path

import pytest
from django.core.files.base import ContentFile
from PIL import Image

from storage.utils.file import get_md5_from_file
from tests import fake


def get_avatar_file(suffix=".jpg"):
    image = Image.new("RGB", (100, 100))

    tmp_file = tempfile.NamedTemporaryFile(suffix=suffix)
    image.save(tmp_file)
    tmp_file.seek(0)

    return tmp_file


@pytest.fixture()
def avatar_file():
    return get_avatar_file()


@pytest.fixture()
def avatar_content_file() -> ContentFile:
    return ContentFile(get_avatar_file(suffix=".png").read(), name="test_avatar.png")


@pytest.fixture(scope="session")
def mixed_format_zipfile(temp_dir) -> dict[Path, str, int]:
    zip_file_dir = temp_dir / "zip_file"
    zip_filename = temp_dir / "zip_file/mixed_format_archive.zip"

    Path.mkdir(temp_dir / "zip_file", parents=True, exist_ok=True)

    json_dir = zip_file_dir / "json"
    Path.mkdir(json_dir, parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_filename, "w") as zip_file:
        for i in range(fake.random_int(min=5, max=20)):
            file_name = f"zip_file/json/file{i+1}.json"
            file_path = temp_dir / file_name
            with file_path.open("w") as f:
                json.dump(
                    fake.json(
                        data_columns=[
                            ("Name", "name"),
                            ("Address", "address"),
                            ("City", "city"),
                            ("Points", "pyint", {"min_value": 50, "max_value": 100}),
                        ],
                        num_rows=fake.random_int(min=50, max=250),
                    ),
                    f,
                )
            zip_file.write(file_path, file_name)

        for i in range(fake.random_int(min=5, max=20)):
            file_name = f"file{i+1}.csv"
            file_path = temp_dir / file_name
            with file_path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(
                    fake.csv(
                        header=("Name", "Address", "City", "Language", "Favorite Color"),
                        data_columns=("{{name}}", "{{address}}", "{{city}}", "{{language_code}}", "{{color_name}}"),
                        num_rows=fake.random_int(min=50, max=250),
                        include_row_ids=False,
                    )
                )
            zip_file.write(file_path, file_name)

        # Add 5 image files
        for i in range(20, 25):
            file_name = f"image{i-19}.png"
            file_path = temp_dir / file_name
            with file_path.open("wb") as f:
                f.write(
                    fake.image(
                        size=(fake.random_int(min=1, max=1024), fake.random_int(min=1, max=2048)),
                        hue="purple",
                        luminosity="bright",
                        image_format="png",
                    )
                )
            zip_file.write(file_path, file_name)

    return {
        "file": zip_filename,
        "etag": get_md5_from_file(zip_filename),
        "size": zip_filename.stat().st_size,
        "content_type": "application/zip",
    }
