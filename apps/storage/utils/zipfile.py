import datetime
import os
from functools import reduce
from pathlib import Path
from zipfile import ZipFile

from django.db.models.fields.files import FieldFile


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


def get_files_and_directories_in_zipfile(zip_file: str | os.PathLike | FieldFile) -> list[dict]:
    """
    Reading a zipfile and returns the information about which files and directories are in the archive
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
