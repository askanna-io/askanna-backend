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
        # fields = "__all__"
        exclude = ["storage_location"]


class PackageSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")

    def get_created_by(self, instance):
        user = instance.created_by
        if user:
            return {
                "name": user.get_name(),
                "uuid": str(user.uuid),
                "short_uuid": str(user.short_uuid),
            }

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

    class Meta:
        model = Package
        # fields = "__all__"
        exclude = ["storage_location"]


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"


class PackageSerializerDetail(BaseArchiveDetailSerializer):
    class Meta:
        model = Package
        fields = "__all__"
