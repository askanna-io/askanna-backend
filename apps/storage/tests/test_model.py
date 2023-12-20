from unittest.mock import Mock

import pytest

from storage.models import File, get_upload_file_to


class TestModelUtils:
    def test_get_upload_file_to(self):
        mock_instance = Mock()

        mock_instance.upload_to = None
        assert get_upload_file_to(mock_instance, "test.txt") == "uploads/test.txt"

        mock_instance.upload_to = "test"
        assert get_upload_file_to(mock_instance, "test.txt") == "test/test.txt"


class TestModelFile:
    def test_file_upload_to(self, test_users):
        file = File.objects.create(
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        assert "avatars" in file.upload_to
        file.delete()

        file = File.objects.create(
            upload_to="test",
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        assert file.upload_to == "test"
        file.delete()

    def test_file_is_zipfile(self, test_users, test_storage_files):
        file = File.objects.create(
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        assert file.is_zipfile is False
        file.delete()

        file = File.objects.create(
            content_type="application/zip",
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        assert file.is_zipfile is False
        file.delete()

        file = test_storage_files["file_private_project_with_config"]
        assert file.is_zipfile is True

    def test_file_zipfile_namelist(self, test_storage_files):
        file = test_storage_files["file_private_project_with_config"]
        assert "askanna.yml" in file.zipfile_namelist

    def test_file_zipfile_namelist_no_zip_file(self, test_users):
        file = File.objects.create(
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        with pytest.raises(AssertionError) as exc:
            file.zipfile_namelist  # noqa: B018

        assert "File is not a Zipfile" in str(exc.value)
        file.delete()

    def test_file_get_file_from_zipfile(self, test_storage_files):
        file = test_storage_files["file_private_project_with_config"]
        file_from_zipfile = file.get_file_from_zipfile("askanna.yml")
        assert len(file_from_zipfile.read()) == 376

    def test_file_get_file_from_zipfile_invalid_file(self, test_storage_files):
        file = test_storage_files["file_private_project_with_config"]
        with pytest.raises(FileNotFoundError):
            file.get_file_from_zipfile("test.txt")

    def test_file_get_file_from_zipfile_no_zip_file(self, test_users):
        file = File.objects.create(
            created_for=test_users["workspace_admin"],
            created_by=test_users["workspace_admin"],
        )
        with pytest.raises(AssertionError) as exc:
            file.get_file_from_zipfile("askanna.yml")

        assert "File is not a Zipfile" in str(exc.value)
        file.delete()
