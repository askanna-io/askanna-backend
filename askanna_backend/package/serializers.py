import datetime
from functools import reduce
import os

from django.conf import settings
from rest_framework import serializers
from zipfile import ZipFile

from core.serializers import BaseArchiveDetailSerializer
from package.models import Package, ChunkedPackagePart


class PackageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = "__all__"


class PackageSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")

    def get_created_by(self, instance):
        user = instance.created_by
        member = instance.member
        if user:
            if member:
                return member.relation_to_json
            return user.relation_to_json

        return {
            "name": "",
            "uuid": "",
            "short_uuid": "",
        }

    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        project = instance.project
        return {
            "name": project.name,
            "uuid": str(project.uuid),
            "short_uuid": str(project.short_uuid),
        }

    filename = serializers.SerializerMethodField("get_filename")

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    class Meta:
        model = Package
        fields = "__all__"


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"


class PackageSerializerDetail(BaseArchiveDetailSerializer):

    filename = serializers.SerializerMethodField("get_filename")

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    class Meta:
        model = Package
        fields = "__all__"
