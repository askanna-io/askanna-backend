# -*- coding: utf-8 -*-
import os
import re
from wsgiref.util import FileWrapper

from django.http import StreamingHttpResponse, HttpResponse
from rest_framework import status


# https://gist.github.com/dcwatson/cb5d8157a8fa5a4a046e
range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)


class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, "close"):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data


def stream(request, path, content_type, size):
    range_header = request.META.get("HTTP_RANGE", "").strip()
    range_match = range_re.match(range_header)
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(
            RangeFileWrapper(open(path, "rb"), offset=first_byte, length=length),
            status=status.HTTP_206_PARTIAL_CONTENT,
            content_type=content_type,
        )
        resp["Content-Length"] = str(length)
        resp["Content-Range"] = "bytes %s-%s/%s" % (first_byte, last_byte, size)
    else:
        try:
            resp = StreamingHttpResponse(
                FileWrapper(open(path, "rb")), content_type=content_type
            )
        except FileNotFoundError:
            resp = HttpResponse(b"", content_type=content_type)

        resp["Content-Length"] = str(size)
    resp["Accept-Ranges"] = "bytes"
    return resp
