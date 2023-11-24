import datetime
import os
import re
import zoneinfo
from functools import reduce
from pathlib import Path
from wsgiref.util import FileWrapper
from zipfile import ZipFile

import croniter
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db.models.fields.files import FieldFile
from django.http import HttpResponseNotFound, StreamingHttpResponse
from jinja2 import Environment, select_autoescape
from rest_framework import status


def parse_string(string: str, variables: dict) -> str:
    env = Environment(variable_start_string="${", variable_end_string="}", autoescape=select_autoescape())
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


def parse_cron_line(cron_line: str | dict) -> str:
    """
    Parse raw cron line and if it's valid return the cron definition. If it's not valid, raise a ValueError.

    The parses determines which format the raw cron line is. It can be one of the following:
    - "* * * * *"  (m, h, d, m, weekday)
    - "@string" (@yearly, @annually, @daily, @hourly, etc.)
    - dict (key, value with keys: minute, hour, day, month, weekday)
    """

    if isinstance(cron_line, str):
        cron_line_parsed = cron_line.strip()

        if cron_line_parsed.startswith("@"):
            # "translate" @string variants
            alias_mapping = {
                "@midnight": "0 0 * * *",
                "@yearly": "0 0 1 1 *",
                "@annually": "0 0 1 1 *",
                "@monthly": "0 0 1 * *",
                "@weekly": "0 0 * * 0",
                "@daily": "0 0 * * *",
                "@hourly": "0 * * * *",
            }
            cron_line_parsed = alias_mapping.get(cron_line_parsed, None)

            if cron_line_parsed is None:
                raise ValueError(
                    "Invalid cron_line alias `%s`. Supported aliases are `%s`.",
                    cron_line,
                    ", ".join(alias_mapping.keys()),
                )

    elif isinstance(cron_line, dict):
        # Check whether we have valid keys, if one invalid key is found, raise an error
        valid_keys = {"minute", "hour", "day", "month", "weekday"}
        invalid_keys = set(cron_line.keys()) - valid_keys

        if len(invalid_keys):
            raise ValueError(
                "Invalid cron_line key(s) are used `%s`. Supported keys are `{}`.",
                ", ".join(invalid_keys),
                ", ".join(valid_keys),
            )

        cron_line_parsed = "{minute} {hour} {day} {month} {weekday}".format(
            minute=cron_line.get("minute", "0"),
            hour=cron_line.get("hour", "0"),
            day=cron_line.get("day", "*"),
            month=cron_line.get("month", "*"),
            weekday=cron_line.get("weekday", "*"),
        )

    else:
        raise ValueError(
            "Invalid cron_line type `%s`. Supported types are `str` and `dict`.",
            type(cron_line).__name__,
        )

    if validate_cron_line(cron_line_parsed):
        return cron_line_parsed

    raise ValueError(
        "Invalid parsed cron_line `%s`.\n  cron_line: `%s`\n  parsed_cron_line: `%s`.",
        cron_line,
        cron_line,
        cron_line_parsed,
    )


def is_valid_timezone(timezone: str) -> bool:
    """Validate whether the timezone specified is a valid one"""
    return timezone in zoneinfo.available_timezones()


def is_valid_email(email: str) -> bool:
    """Validate whether the email specified is a valid one"""
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


def get_items_in_zip_file(zip_file: str | os.PathLike | FieldFile) -> tuple[list, list]:
    """
    Reading a zip archive and returns a list with items and a list with paths in the zip file.
    """
    files_in_zip = []
    dirs_in_zip = []

    if not isinstance(zip_file, FieldFile):
        zip_file = Path(zip_file)

    with ZipFile(zip_file) as zip_file_object:
        for item in zip_file_object.infolist():
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
                dirs_in_zip.append(item.filename)
                continue

            filename_parts = item.filename.split("/")
            filename_path = "/".join(filename_parts[: len(filename_parts) - 1])
            name = item.filename.replace(filename_path + "/", "")

            dirs_in_zip.append(filename_path)

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

            files_in_zip.append(zip_item)

    return files_in_zip, dirs_in_zip


def get_all_directories(paths: list) -> list[str]:
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

    return sorted(list(set(directories) - {"/"} - {""}))


def get_files_and_directories_in_zip_file(zip_file: str | os.PathLike | FieldFile) -> list[dict]:
    """
    Reading a zip archive and returns the information about which files and directories are in the archive
    """
    files_in_zip, dirs_in_zip = get_items_in_zip_file(zip_file)
    directories_in_zip = get_all_directories(dirs_in_zip)

    for directory in directories_in_zip:
        directory_parts = directory.split("/")
        directory_path = "/".join(directory_parts[: len(directory_parts) - 1])
        name = directory.replace(directory_path + "/", "")

        if not name:
            # If the name is blank, there is nothing to add
            continue

        files_in_zip.append(
            {
                "path": directory,
                "parent": directory_path or "/",
                "name": name,
                "size": get_directory_size_from_filelist(directory, files_in_zip),
                "type": "directory",
                "last_modified": get_last_modified_in_directory(directory, files_in_zip),
            }
        )

    return sorted(files_in_zip, key=lambda x: (x["type"].lower(), x["name"].lower()))


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
