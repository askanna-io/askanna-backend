import datetime
from functools import reduce
import os


from django.conf import settings
from rest_framework import serializers
from zipfile import ZipFile

from package.models import Package, ChunkedPackagePart


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"


class PackageSerializerDetail(serializers.ModelSerializer):
    files = serializers.SerializerMethodField("get_files_for_package")
    cdn_base_url = serializers.SerializerMethodField("get_base_url")

    class Meta:
        model = Package
        fields = "__all__"

    def get_base_url(self, instance):
        """
            Generate the url for where to find the "blob" files of the package.
            This url points to the extracted version of the package hosted at the CDN server.
            Please note the /files/blob/ prefix
        """
        return "https://{FQDN}/files/blob/{LOCATION}".format(
                FQDN=settings.ASKANNA_CDN_FQDN,
                LOCATION=instance.uuid
            )

    def get_files_for_package(self, instance):
        """
            On the fly reading a zip archive and returns the information about what files are in the archive
        """
        filelist = []
        with ZipFile(
            os.path.join(settings.PACKAGES_ROOT, instance.storage_location)
        ) as zippackage:
            for f in zippackage.infolist():
                if (
                    f.filename.startswith(".git/")
                    or f.filename.endswith(".pyc")
                    or ".egg-info" in f.filename
                ):
                    continue
                fpath_parts = f.filename.split("/")
                fpath = "/".join(fpath_parts[: len(fpath_parts) - 1])
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
        directories = list(set(map(lambda x: x["parent"], filelist)))

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
                        filter(lambda x: x["parent"] == d, filelist),
                        0,
                    ),
                    "last_modified": datetime.datetime.now(),
                    "type": "directory",
                }
            )

        return dirlist + filelist
