import datetime
import json
import os
import re
import zoneinfo
from functools import reduce
from pathlib import Path
from wsgiref.util import FileWrapper
from zipfile import ZipFile

import croniter
import filetype
import magic
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpResponseNotFound, StreamingHttpResponse
from jinja2 import Environment
from rest_framework import status


def parse_string(string, variables):
    env = Environment(variable_start_string="${", variable_end_string="}")  # nosec: B701
    template = env.from_string(string)
    return template.render(variables)


def validate_cron_line(cron_line: str) -> bool:
    """
    We validate the cron expression with croniter
    """
    try:
        return croniter.croniter.is_valid(cron_line)
    except AttributeError:
        return False


def parse_cron_line(cron_line: str) -> str:
    """
    parse incoming cron definition
    if it is valid, then return the cron_line, otherwise a None
    """

    if isinstance(cron_line, str):
        # we deal with cron strings
        # first check whether we need to make a "translation" for @strings

        alias_mapping = {
            "@midnight": "0 0 * * *",
            "@yearly": "0 0 1 1 *",
            "@annually": "0 0 1 1 *",
            "@monthly": "0 0 1 * *",
            "@weekly": "0 0 * * 0",
            "@daily": "0 0 * * *",
            "@hourly": "0 * * * *",
        }
        cron_line = alias_mapping.get(cron_line.strip(), cron_line.strip())

    elif isinstance(cron_line, dict):
        # we deal with dictionary
        # first check whether we have valid keys, if one invalid key is found, return None
        valid_keys = {"minute", "hour", "day", "month", "weekday"}
        invalid_keys = set(cron_line.keys()) - valid_keys
        if len(invalid_keys):
            return None
        cron_line = "{minute} {hour} {day} {month} {weekday}".format(
            minute=cron_line.get("minute", "0"),
            hour=cron_line.get("hour", "0"),
            day=cron_line.get("day", "*"),
            month=cron_line.get("month", "*"),
            weekday=cron_line.get("weekday", "*"),
        )

    if not validate_cron_line(cron_line):
        return None

    return cron_line


def parse_cron_schedule(schedule: list):
    """
    Determine which format it has, it can be one of the following:
    - * * * * *  (m, h, d, m, weekday)
    - @annotation (@yearly, @annually, @monthly, @weekly, @daily, @hourly)
    - dict (k,v with: minute,hour,day,month,weekday)
    """

    for cron_line in schedule:
        yield cron_line, parse_cron_line(cron_line)


# File mimetype detection logic
def is_jsonfile(filepath: Path) -> bool:
    """
    Determine whether we are dealing with a JSON file
    returns True/False
    """

    try:
        json.load(filepath.open())
    except json.decoder.JSONDecodeError:
        return False
    return True


def detect_file_mimetype(filepath: Path) -> str:
    """
    Use libmagic to determine what file we find on `filepath`. If the mimetype is text/plain, we do an additional check
    to see if it is a JSON file. If so, we return application/json.
    """

    detected_mimetype = magic.from_file(filepath, mime=True)

    if not detected_mimetype:
        filetype_guess = filetype.guess(filepath)
        if filetype_guess:
            detected_mimetype = filetype_guess.mime

    if detected_mimetype and detected_mimetype == "text/plain":
        if is_jsonfile(filepath):
            detected_mimetype = "application/json"

    return detected_mimetype


# date timezone validation
def is_valid_timezone(timezone, default=settings.TIME_ZONE):
    """
    Validate whether the timezone specified is a valid one
    If not, return the default timezone.
    """
    if timezone in zoneinfo.available_timezones():
        return timezone
    return default


def is_valid_email(email):
    try:
        validate_email(email)
    except ValidationError:
        return False
    else:
        return True


def pretty_time_delta(seconds: int) -> str:
    """
    Transforms an integer which represents duration into a human readable string
    """
    seconds = int(seconds)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    def plurify(amount, single, plural):
        if amount == 1:
            return f"{amount} {single}"
        return f"{amount} {plural}"

    if days > 0:
        return "{}, {}, {} and {}".format(
            plurify(days, "day", "days"),
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    if hours > 0:
        return "{}, {} and {}".format(
            plurify(hours, "hour", "hours"),
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )
    if minutes > 0:
        return "{} and {}".format(
            plurify(minutes, "minute", "minutes"),
            plurify(seconds, "second", "seconds"),
        )

    return "{}".format(plurify(seconds, "second", "seconds"))


def flatten(t):
    return [item for sublist in t for item in sublist]


def get_last_modified_in_directory(directory: str, filelist: list) -> datetime.datetime:
    latest_modified = datetime.datetime(1970, 1, 1, 0, 0, 0)
    files = [file for file in filelist if file["parent"].startswith(directory)]

    # If the directory does not contain any files, we use the latest modified date in the filelist as last modified
    # date for the directory
    if not files:
        files = filelist

    for f in files:
        if f.get("last_modified") > latest_modified:
            latest_modified = f.get("last_modified")

    return latest_modified


def get_directory_size_from_filelist(directory: str, filelist: list) -> int:
    """
    Get the size of a directory by summing the size of all the files in the directory. The sum also includes the files
    in subdirectories.
    """
    return reduce(
        lambda x, y: x + y["size"],
        filter(lambda x: x["path"].startswith(directory + "/") and x["type"] == "file", filelist),
        0,
    )


def get_items_in_zip_file(zip_file_path: str | os.PathLike) -> tuple[list, list]:
    """
    Reading a zip archive and returns a list with items and a list with paths in the zip file.
    """
    zip_files = []
    zip_paths = []
    with ZipFile(Path(zip_file_path), mode="r") as zip_file:
        for item in zip_file.infolist():
            if (
                item.filename.startswith(".git/")
                or item.filename.startswith(".askanna/")
                or item.filename.startswith("__MACOSX/")
                or item.filename.endswith(".pyc")
                or ".egg-info" in item.filename
            ):
                # Hide files and directories that we don't want to appear in the result list
                continue

            if item.is_dir():
                zip_paths.append(item.filename)
                continue

            filename_parts = item.filename.split("/")
            filename_path = "/".join(filename_parts[: len(filename_parts) - 1])
            name = item.filename.replace(filename_path + "/", "")

            zip_paths.append(filename_path)

            if not name:
                # If the name becomes blank, we remove the entry
                continue

            zip_item = {
                "path": item.filename,
                "parent": filename_path or "/",
                "name": name,
                "size": item.file_size,
                "type": "file",
                "last_modified": datetime.datetime(*item.date_time),
            }

            zip_files.append(zip_item)

    return zip_files, zip_paths


def get_all_directories(paths: list) -> list:
    """
    Get a list of all directories from a list of paths. By unwinding the paths we make sure that all (sub)directories
    are available in the list of directories we return.
    """

    directories = []
    for path in paths:
        directories.append(path)

        path_parts = path.split("/")
        while len(path_parts) > 1:
            path_parts = path_parts[: len(path_parts) - 1]
            path = "/".join(path_parts)
            if path and path != "/":
                directories.append(path)

    directories = sorted(list(set(directories) - {"/"} - {""}))

    return directories


def get_files_and_directories_in_zip_file(zip_file_path: str | os.PathLike) -> list:
    """
    Reading a zip archive and returns the information about which files and directories are in the archive
    """

    zip_files, zip_paths = get_items_in_zip_file(zip_file_path)
    zip_directories = get_all_directories(zip_paths)

    for zip_dir in zip_directories:
        zip_dir_parts = zip_dir.split("/")
        zip_dir_path = "/".join(zip_dir_parts[: len(zip_dir_parts) - 1])
        name = zip_dir.replace(zip_dir_path + "/", "")

        if not name:
            # If the name becomes blank, we remove the entry
            continue

        zip_files.append(
            {
                "path": zip_dir,
                "parent": zip_dir_path or "/",
                "name": name,
                "size": get_directory_size_from_filelist(zip_dir, zip_files),
                "type": "directory",
                "last_modified": get_last_modified_in_directory(zip_dir, zip_files),
            }
        )

    return sorted(zip_files, key=lambda x: (x["type"].lower(), x["name"].lower()))


# The 'RangeFileWrapper' class and method 'stream' is used to setup streaming of content via an REST API endpoint
class RangeFileWrapper:
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

        if self.remaining <= 0:
            raise StopIteration()

        data = self.filelike.read(min(self.remaining, self.blksize))

        if not data:
            raise StopIteration()

        self.remaining -= len(data)
        return data


def stream(request, path, content_type, size):
    range_header = request.META.get("HTTP_RANGE", "").strip()

    # https://gist.github.com/dcwatson/cb5d8157a8fa5a4a046e
    range_re = re.compile(r"bytes\s*=\s*(\d+)\s*-\s*(\d*)", re.I)
    range_match = range_re.match(range_header)

    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(
            RangeFileWrapper(Path.open(path, "rb"), offset=first_byte, length=length),
            status=status.HTTP_206_PARTIAL_CONTENT,
            content_type=content_type,
        )
        resp["Content-Length"] = str(length)
        resp["Content-Range"] = f"bytes {first_byte}-{last_byte}/{size}"
    else:
        try:
            resp = StreamingHttpResponse(FileWrapper(Path.open(path, "rb")), content_type=content_type)
        except FileNotFoundError:
            return HttpResponseNotFound()

        resp["Content-Length"] = str(size)
    resp["Accept-Ranges"] = "bytes"
    return resp
