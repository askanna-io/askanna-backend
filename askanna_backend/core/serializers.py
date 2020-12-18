import datetime
from functools import reduce
import os


from django.conf import settings
from rest_framework import serializers
from zipfile import ZipFile


class BaseArchiveDetailSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField("get_files_for_archive")
    cdn_base_url = serializers.SerializerMethodField("get_base_url")

    def get_base_url(self, instance):
        """
            Generate the url for where to find the "blob" files of the package.
            This url points to the extracted version of the archive hosted at the CDN server.
            Please note the /files/blob/ prefix
        """
        return "{BASE_URL}/files/blob/{LOCATION}".format(
            BASE_URL=settings.ASKANNA_CDN_URL, LOCATION=instance.uuid
        )

    def get_files_for_archive(self, instance):
        """
            On the fly reading a zip archive and returns the information about what files are in the archive
        """
        filelist = []
        parents = []
        with ZipFile(os.path.join(instance.stored_path)) as zippackage:
            for f in zippackage.infolist():
                if (
                    f.filename.startswith(".git/")
                    or f.filename.startswith(".askanna/")
                    or f.filename.endswith(".pyc")
                    or ".egg-info" in f.filename
                ):
                    continue
                fpath_parts = f.filename.split("/")
                fpath = "/".join(fpath_parts[:len(fpath_parts) - 1])
                parents.append(fpath)
                r = {
                    "path": f.filename,
                    "parent": fpath or "/",
                    "name": f.filename.replace(fpath + "/", ""),
                    "is_dir": f.is_dir(),
                    "size": f.file_size,
                    "last_modified": datetime.datetime(*f.date_time),
                    "type": "directory" if f.is_dir() else "file",
                }

                filelist.append(r)

        # also get all directories
        # "unwind" all directories, it can be the case that directories only contain directories
        # which will cause this not te be listed in the zip
        # let's fix this
        directories = []
        for parent in parents:
            # just add the parent of this parent back
            fpath_parts = parent.split("/")
            directories.append(parent)
            directories.append("/".join(fpath_parts[:len(fpath_parts) - 1]))
        directories = sorted(list(set(directories) - set(["/"]) - set([""])))

        dirlist = []
        for d in directories:
            path_elements = d.split("/")
            parent = "/".join(path_elements[: len(path_elements) - 1])

            dirlist.append(
                {
                    "path": d,
                    "parent": parent or "/",
                    "name": d.replace(parent + "/", ""),
                    "is_dir": True,
                    "size": reduce(
                        lambda x, y: x + y["size"],
                        filter(lambda x: x["path"].startswith(d + "/"), filelist),
                        0,
                    ),
                    "last_modified": datetime.datetime.now(),
                    "type": "directory",
                }
            )

        return dirlist + filelist
