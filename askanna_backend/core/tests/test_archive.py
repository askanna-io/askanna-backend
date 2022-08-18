import datetime
import unittest

from core.utils import (
    get_all_directories,
    get_directory_size_from_filelist,
    get_files_and_directories_in_zip_file,
    get_items_in_zip_file,
    get_last_modified_in_directory,
)
from django.conf import settings

filelist = [
    {
        "path": "README.md",
        "parent": "/",
        "name": "README.md",
        "size": 1821,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "requirements.txt",
        "parent": "/",
        "name": "requirements.txt",
        "size": 49,
        "type": "file",
        "last_modified": datetime.datetime(2020, 10, 7, 21, 16),
    },
    {
        "path": "askanna.yml",
        "parent": "/",
        "name": "askanna.yml",
        "size": 967,
        "type": "file",
        "last_modified": datetime.datetime(2021, 2, 17, 10, 57, 28),
    },
    {
        "path": "docs/README.md",
        "parent": "docs",
        "name": "README.md",
        "size": 1318,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 47, 24),
    },
    {
        "path": "docs/.nojekyll",
        "parent": "docs",
        "name": ".nojekyll",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 46, 10),
    },
    {
        "path": "docs/sidebar.md",
        "parent": "docs",
        "name": "sidebar.md",
        "size": 20,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 40),
    },
    {
        "path": "docs/index.html",
        "parent": "docs",
        "name": "index.html",
        "size": 2387,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 40),
    },
    {
        "path": "docs/media/askanna.png",
        "parent": "docs/media",
        "name": "askanna.png",
        "size": 22130,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 43),
    },
    {
        "path": "docs/media/favicon.ico",
        "parent": "docs/media",
        "name": "favicon.ico",
        "size": 6782,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 43),
    },
    {
        "path": "result/evaluation.json",
        "parent": "result",
        "name": "evaluation.json",
        "size": 85,
        "type": "file",
        "last_modified": datetime.datetime(2020, 8, 4, 11, 21, 28),
    },
    {
        "path": "result/prediction.json",
        "parent": "result",
        "name": "prediction.json",
        "size": 86,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 14, 6, 44),
    },
    {
        "path": "result/.gitkeep",
        "parent": "result",
        "name": ".gitkeep",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 14, 3, 56),
    },
    {
        "path": "data/interim/.gitkeep",
        "parent": "data/interim",
        "name": ".gitkeep",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 4, 3, 10, 15, 26),
    },
    {
        "path": "data/input/.gitkeep",
        "parent": "data/input",
        "name": ".gitkeep",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 4, 7, 9, 0, 36),
    },
    {
        "path": "data/processed/.gitkeep",
        "parent": "data/processed",
        "name": ".gitkeep",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 4, 7, 9, 0, 46),
    },
    {
        "path": "src/__init__.py",
        "parent": "src",
        "name": "__init__.py",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "src/models/train_model.py",
        "parent": "src/models",
        "name": "train_model.py",
        "size": 390,
        "type": "file",
        "last_modified": datetime.datetime(2020, 11, 10, 16, 4, 30),
    },
    {
        "path": "src/models/evaluate_model.py",
        "parent": "src/models",
        "name": "evaluate_model.py",
        "size": 234,
        "type": "file",
        "last_modified": datetime.datetime(2020, 8, 4, 11, 20, 28),
    },
    {
        "path": "src/models/serve_model.py",
        "parent": "src/models",
        "name": "serve_model.py",
        "size": 234,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "src/models/test-multiple-models.py",
        "parent": "src/models",
        "name": "test-multiple-models.py",
        "size": 4159,
        "type": "file",
        "last_modified": datetime.datetime(2021, 2, 2, 15, 4, 42),
    },
    {
        "path": "src/models/__init__.py",
        "parent": "src/models",
        "name": "__init__.py",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "src/data/create_dataset.py",
        "parent": "src/data",
        "name": "create_dataset.py",
        "size": 899,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "src/data/__init__.py",
        "parent": "src/data",
        "name": "__init__.py",
        "size": 0,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
    {
        "path": "src/data/create_features.py",
        "parent": "src/data",
        "name": "create_features.py",
        "size": 234,
        "type": "file",
        "last_modified": datetime.datetime(2020, 6, 25, 8, 42, 2),
    },
]


class TestArchive(unittest.TestCase):
    def test_get_files_and_directories_in_zip_file_from_project_001(self):
        zip_file_path = settings.TEST_RESOURCES_DIR.path("projects/project-001.zip")
        zip_files = get_files_and_directories_in_zip_file(zip_file_path)

        self.assertEqual(len(zip_files), 3)

    def test_get_items_in_zip_file_from_project_001(self):
        zip_file_path = settings.TEST_RESOURCES_DIR.path("projects/project-001.zip")
        zip_files, zip_paths = get_items_in_zip_file(zip_file_path)

        self.assertEqual(len(zip_files), 3)
        self.assertEqual(len(zip_paths), 3)

    def test_get_all_directories_from_project_001(self):
        # Project 001 contain 0 directories
        zip_file_path = settings.TEST_RESOURCES_DIR.path("projects/project-001.zip")
        _, zip_paths = get_items_in_zip_file(zip_file_path)
        zip_directories = get_all_directories(zip_paths)

        self.assertEqual(len(zip_directories), 0)

    def test_get_files_and_directories_in_zip_file_from_artifact_aa(self):
        zip_file_path = settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip")
        zip_files = get_files_and_directories_in_zip_file(zip_file_path)

        self.assertEqual(len(zip_files), 3)

    def test_get_items_in_zip_file_from_artifact_aa(self):
        zip_file_path = settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip")
        zip_files, zip_paths = get_items_in_zip_file(zip_file_path)

        self.assertEqual(len(zip_files), 2)
        self.assertEqual(len(zip_paths), 3)

    def test_get_all_directories_from_artifact_aa(self):
        # Artifact AA contains a file test.pyc that should be excluded and a directory that should be included
        zip_file_path = settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip")
        _, zip_paths = get_items_in_zip_file(zip_file_path)
        zip_directories = get_all_directories(zip_paths)

        self.assertEqual(len(zip_directories), 2)

    def test_last_modified(self):
        expected_last_modified = datetime.datetime(2020, 6, 25, 8, 47, 24)
        found_last_modified = get_last_modified_in_directory("docs", filelist)

        self.assertEqual(found_last_modified, expected_last_modified)

    def test_last_modified_empty_dir(self):
        expected_last_modified = datetime.datetime(2020, 12, 16, 1, 13, 12)
        zip_file_path = settings.TEST_RESOURCES_DIR.path("artifacts/artifact-aa.zip")
        filelist, _ = get_items_in_zip_file(zip_file_path)
        found_last_modified = get_last_modified_in_directory("models", filelist)

        self.assertEqual(found_last_modified, expected_last_modified)

    def test_get_directory_size_from_filelist(self):
        size = get_directory_size_from_filelist("docs", filelist)

        self.assertEqual(size, 32637)
