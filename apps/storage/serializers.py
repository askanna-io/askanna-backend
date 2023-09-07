from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from core.serializers import RelationSerializer
from storage.models import File


class FileURLField(serializers.HyperlinkedIdentityField):
    view_name = "storage-file-download"
    lookup_field = "suuid"

    def __init__(self, *args, **kwargs):
        kwargs["view_name"] = self.view_name
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        if settings.ASKANNA_FILE_DOWNLOAD_VIA_DJANGO:
            return super().to_representation(value)

        return value.file.url


class FileDownloadInfoSerializer(serializers.ModelSerializer):
    url = FileURLField()
    type = serializers.SerializerMethodField(
        help_text="The type of service that handles the download (askanna, cdn or minio)"
    )

    def get_type(self, obj) -> str:
        if settings.ASKANNA_FILE_DOWNLOAD_VIA_DJANGO:
            return "askanna"

        if settings.ASKANNA_FILESTORAGE == "filesystem":
            return "cdn"

        return settings.ASKANNA_FILESTORAGE

    class Meta:
        model = File
        fields = ["type", "url"]


class FileInfoSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField()
    content_type = serializers.CharField(source="file.file.content_type")
    size = serializers.IntegerField(source="file.file.size")
    download_info = FileDownloadInfoSerializer(source="*")
    created_for = RelationSerializer()
    created_by = RelationSerializer()

    def get_filename(self, obj) -> str | None:
        if obj.name:
            return obj.name

        file_object = obj.file.file
        if hasattr(file_object, "name"):
            return Path(file_object.name).name

        # This should never happen, but just in case
        return None  # pragma: no cover

    class Meta:
        model = File
        fields = [
            "suuid",
            "filename",
            "content_type",
            "size",
            "download_info",
            "created_for",
            "created_by",
            "created_at",
            "modified_at",
        ]
