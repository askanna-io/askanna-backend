from unittest.mock import MagicMock

from storage.file import File, MultipartFile


class TestFile:
    def test_content_type(self, avatar_file):
        file = File(avatar_file)
        assert file.content_type == "image/jpeg"


class TestMultipartFile:
    def test_size(self):
        mock_file = MagicMock()
        mock_file.name = "avatar.jpg"

        mock_file.storage = MagicMock()
        mock_file.storage.support_chunks = True
        mock_file.storage.open = MagicMock()
        mock_file.storage.open.return_value = MagicMock()
        mock_file.storage.open.return_value.__enter__.return_value.size = 10

        mock_file.instance = MagicMock()
        mock_file.instance.part_filenames = ["part_0001.part", "part_0002.part"]
        mock_file.instance.upload_to = "upload"

        file = MultipartFile(mock_file)
        assert file.size == 20
