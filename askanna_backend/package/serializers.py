import datetime
import os

from django.conf import settings
from rest_framework import serializers
from zipfile import ZipFile

from package.models import Package, ChunkedPackagePart


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = (
            "uuid",
            "filename",
            "storage_location",
            "project_id",
            "size",
            "created_by",
            "created_at",
        )


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = (
            "uuid",
            "filename",
            "size",
            "file_no",
            "is_last",
            "package",
            "created_at",
        )


class PackageSerializerDetail(serializers.ModelSerializer):
    files = serializers.SerializerMethodField('get_files_for_package')
    class Meta:
        model = Package
        fields = (
            "uuid",
            "filename",
            "storage_location",
            "project_id",
            "size",
            "created_by",
            "created_at",
            "files"
        )

    def get_files_for_package(self, instance):
        """
            On the fly reading a zip archive and returns the information about what files are in the archive
        """
        filelist = []
        with ZipFile(os.path.join(settings.PACKAGES_ROOT, instance.storage_location)) as zippackage:
            for f in zippackage.infolist():
                if f.filename.startswith(".git/") or f.filename.endswith(".pyc") or ".egg-info" in f.filename:
                    continue
                fpath_parts = f.filename.split("/")
                fpath = "/".join(fpath_parts[:len(fpath_parts)-1])
                r = {
                    "path": f.filename,
                    "parent": fpath or "/",
                    "name": f.filename.replace(fpath+"/", ""),
                    "is_dir": f.is_dir(),
                    "size": f.file_size,
                    "last_modified": datetime.datetime(*f.date_time),
                    "type": "directory" if f.is_dir() else "file"
                }
                filelist.append(r)
        return filelist
