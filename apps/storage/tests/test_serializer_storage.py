from unittest.mock import MagicMock, patch

import pytest
from rest_framework import serializers

from storage.serializers import FileUploadPartSerializer


class TestFilePartSerializer:
    def test_validate_etag(self, mixed_format_zipfile):
        data = {
            "part": mixed_format_zipfile["file"],
            "part_number": 1,
            "etag": mixed_format_zipfile["etag"],
        }
        serializer = FileUploadPartSerializer(data=data)

        assert serializer.validate_etag(mixed_format_zipfile["etag"]) == mixed_format_zipfile["etag"]

        # Test with an invalid ETag value
        with pytest.raises(serializers.ValidationError):
            serializer.validate_etag(-1)

    @patch("django.core.files.storage.Storage.save", return_value="saved_name")
    def test_save_part_went_wrong_on_saved_name(self, mock_save, avatar_content_file):
        data = {
            "part": avatar_content_file,
            "part_number": 1,
        }
        serializer = FileUploadPartSerializer(instance=MagicMock(), data=data)
        serializer.is_valid(raise_exception=True)

        with pytest.raises(serializers.ValidationError) as excinfo:
            serializer.save_part()

        assert "Something went wrong while saving part '1'." in str(excinfo.value)
