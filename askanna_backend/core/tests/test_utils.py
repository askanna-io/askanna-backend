import pytest
from django.http import HttpResponseNotFound, StreamingHttpResponse
from django.test import RequestFactory

from core.utils.utils import stream


@pytest.fixture
def request_factory():
    return RequestFactory()


def test_stream_success(request_factory, tmp_path):
    # Create a temporary file to stream
    file_path = tmp_path / "test_file.txt"
    file_path.write_text("Hello, world!")

    # Create a request with the file path
    request = request_factory.get("/")
    response = stream(request, file_path, "text/plain", file_path.stat().st_size)

    # Assert that the response has the expected status code and content
    assert response.status_code == 200
    assert isinstance(response, StreamingHttpResponse)
    assert b"Hello, world!" == response.getvalue()


def test_stream_file_not_found(request_factory, tmp_path):
    # Create a request with a non-existent file path
    request = request_factory.get("/")
    response = stream(request, tmp_path / "test_file_not_exist_.txt", "text/plain", 100)
    assert response.status_code == 404
    assert isinstance(response, HttpResponseNotFound)
