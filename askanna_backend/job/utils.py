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
            resp = StreamingHttpResponse(FileWrapper(open(path, "rb")), content_type=content_type)
        except FileNotFoundError:
            resp = HttpResponse(b"", content_type=content_type)

        resp["Content-Length"] = str(size)
    resp["Accept-Ranges"] = "bytes"
    return resp


def get_unique_names_with_data_type(all_keys: list) -> list:
    """
    Make a unique list of names in the list of dictionaries and set data type for each name

    `all_keys` is a list of dictionaries where each dictionary has two keys:
    - name
    - type

    The functon returns a list of dictionaries with unique names and the date type for each name. If data type values
    or not unique, it's set to 'mixed'.
    """
    unique_keys = []

    for key in all_keys:
        add_key = True
        for unique_key in unique_keys:
            if key["name"] == unique_key["name"]:
                add_key = False
                if unique_key.get("count"):
                    unique_key.update({"count": unique_key["count"] + 1})
                if key["type"] != unique_key["type"]:
                    if key["type"] in ("integer", "float") and unique_key["type"] in ("integer", "float"):
                        unique_key.update({"type": "float"})
                    else:
                        unique_key.update({"type": "mixed"})
                break

        if add_key:
            unique_keys.append(key)

    return unique_keys
