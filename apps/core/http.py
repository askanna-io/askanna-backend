from django.http.response import FileResponse
from rest_framework import status


class RangeFileReader:
    """
    A class to read a file-like object in chunks. Useful for streaming file content. The iterator yields chunks of data
    of size `block_size`. The iterator starts reading from `start` and stops at `stop`.

    Args:
        file_like: a file-like object to read from.
        start (Optional[int]): where to start reading the file. Default to beginning of file.
        stop (Optional[int]): where to end reading the file. Defaults to end of file.
        block_size (Optional[int]): The block_size to read per iteration. Defaults to 4096.
    """

    def __init__(self, file_like, start: int = 0, stop: int = -1, block_size: int = 4096):
        self.file_like = file_like
        self.start = start
        self.stop = stop if stop >= 0 else float("inf")
        self.block_size = block_size
        self._size = None

    def __iter__(self):
        self.file_like.seek(self.start)
        position = self.start

        while position <= self.stop:
            data = self.file_like.read(min(self.block_size, self.stop - position))
            if not data:
                break

            yield data

            position += self.block_size

    def close(self):
        if hasattr(self.file_like, "close"):
            self.file_like.close()

    @property
    def size(self):
        if self._size is None:
            if hasattr(self.file_like, "size"):
                self._size = self.file_like.size
            else:
                self._size = len(self.file_like.read())

        return self._size


class RangeFileResponse(FileResponse):
    """
    A streaming HTTP response class optimized for files with support for the Range header.

    The Range header is used to retrieve a range of bytes from a file. A.o. this is used by browsers to
    support resuming of interrupted downloads or to stream media files.
    """

    def __init__(self, file_object, range_header: str, *args, **kwargs):
        if not range_header or not isinstance(range_header, str):
            raise ValueError("Range header is required and must be a string in the format 'bytes=...'.")
        self.range_header = range_header
        self.file_object = RangeFileReader(file_object)

        super().__init__(self.file_object, *args, **kwargs)

        self["Accept-Ranges"] = "bytes"
        self.process_range_header()

    def process_range_header(self):
        """
        Process the range header. For a valid range request, sets the Content-Range header and set the file's position
        indicator to the start of the requested byte range. Also sets the HTTP status_code to 206 (partial content).

        For an invalid range request, sets the HTTP status_code to 416 (requested range not satisfiable).
        """

        if not self.range_header or not self.range_header.startswith("bytes="):
            self.status_code = status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
            return

        _, range_str = self.range_header.split("=", 1)

        try:
            if range_str.startswith("-"):
                first_byte = max(self.file_object.size - int(range_str.lstrip("-")), 0)
                last_byte = self.file_object.size - 1
            elif range_str.endswith("-"):
                first_byte = int(range_str.rstrip("-"))
                last_byte = self.file_object.size - 1
            else:
                first_byte, last_byte = range_str.split("-", 1)
                first_byte = int(first_byte)
                last_byte = int(last_byte)
        except ValueError:
            self.status_code = status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
            return

        if first_byte >= self.file_object.size or first_byte > last_byte:
            self.status_code = status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
            return

        if last_byte >= self.file_object.size:
            last_byte = self.file_object.size - 1

        self.file_object.start = first_byte
        self.file_object.stop = last_byte + 1

        self.status_code = status.HTTP_206_PARTIAL_CONTENT
        self["Content-Length"] = str(last_byte - first_byte + 1)
        self["Content-Range"] = f"bytes {first_byte}-{last_byte}/{self.file_object.size}"
        self["Content-Disposition"] = "inline" + (f"; filename={self.filename}" if self.filename else "")
