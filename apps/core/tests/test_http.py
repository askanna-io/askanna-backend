import io
from http import HTTPStatus

import pytest
from django.test import TestCase

from core.http import RangeFileReader, RangeFileResponse


class TestRangeFileReader:
    def test_iter(self):
        file_obj = io.BytesIO(b"abcdefghijklmnopqrstuvwxyz")
        reader = RangeFileReader(file_obj, start=10, stop=19, block_size=5)
        assert list(reader) == [b"klmno", b"pqrs"]

    def test_iter_no_stop(self):
        file_obj = io.BytesIO(b"abcdefghijklmnopqrstuvwxyz")

        reader = RangeFileReader(file_obj, block_size=5)
        assert list(reader) == [b"abcde", b"fghij", b"klmno", b"pqrst", b"uvwxy", b"z"]

        reader = RangeFileReader(file_obj, start=10, block_size=5)
        assert list(reader) == [b"klmno", b"pqrst", b"uvwxy", b"z"]


class TestRangeFileResponse(TestCase):
    def setUp(self):
        self.file_obj = io.BytesIO(b"abcdefghijklmnopqrstuvwxyz")

    def test_range_header_valid(self):
        range_header = "bytes=10-19"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response["Accept-Ranges"] == "bytes"
        assert response["Content-Length"] == "10"
        assert response["Content-Range"] == "bytes 10-19/26"
        assert response["Content-Disposition"] == "inline"

        assert response.status_code == HTTPStatus.PARTIAL_CONTENT
        assert response.streaming_content, b"klmnopqrst"

    def test_range_header_valid_no_stop(self):
        range_header = "bytes=10-"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response["Accept-Ranges"] == "bytes"
        assert response["Content-Length"] == "16"
        assert response["Content-Range"] == "bytes 10-25/26"
        assert response["Content-Disposition"] == "inline"

        assert response.status_code == HTTPStatus.PARTIAL_CONTENT
        assert response.streaming_content, b"klmnopqrstuvwxyz"

    def test_range_header_valid_last_bytes(self):
        range_header = "bytes=-5"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response["Accept-Ranges"] == "bytes"
        assert response["Content-Length"] == "5"
        assert response["Content-Range"] == "bytes 21-25/26"
        assert response["Content-Disposition"] == "inline"

        assert response.status_code == HTTPStatus.PARTIAL_CONTENT
        assert response.streaming_content, b"vwxyz"

    def test_range_header_last_byte_larger_than_file(self):
        range_header = "bytes=25-100"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response["Accept-Ranges"] == "bytes"
        assert response["Content-Length"] == "1"
        assert response["Content-Range"] == "bytes 25-25/26"
        assert response["Content-Disposition"] == "inline"

        assert response.status_code == HTTPStatus.PARTIAL_CONTENT
        assert response.streaming_content, b"z"

    def test_range_header_first_byte_larger_than_file(self):
        range_header = "bytes=100-200"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    def test_range_header_valid_last_serie_of_bytes(self):
        range_header = "bytes=20-25"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response["Accept-Ranges"] == "bytes"
        assert response["Content-Length"] == "6"
        assert response["Content-Range"] == "bytes 20-25/26"
        assert response["Content-Disposition"] == "inline"

        assert response.status_code == HTTPStatus.PARTIAL_CONTENT
        assert response.streaming_content, b"uvwxyz"

    def test_range_header_invalid(self):
        range_header = "bytes=10-5"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    def test_range_header_invalid_byte_string(self):
        range_header = "bytes=abc"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    def test_range_header_invalid_no_start(self):
        range_header = "byte=1"
        response = RangeFileResponse(self.file_obj, range_header)

        assert response.status_code == HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE

    def test_range_header_empty(self):
        with pytest.raises(ValueError):
            RangeFileResponse(self.file_obj, "")
