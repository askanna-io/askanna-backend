from core.utils import get_files_and_directories_in_zip_file
from django.conf import settings
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


@extend_schema_field(OpenApiTypes.STR)
class ReadWriteSerializerMethodField(serializers.Field):
    """
    Code inspired by https://stackoverflow.com/questions/40555472/django-rest-serializer-method-writable-field
    """

    def __init__(self, method_name=None, **kwargs):
        self.method_name = method_name
        kwargs["source"] = "*"
        kwargs["read_only"] = False
        super().__init__(**kwargs)

    def bind(self, field_name, parent):
        if self.method_name is None:
            self.method_name = f"get_{field_name}"
        super().bind(field_name, parent)

    def to_representation(self, value):
        method = getattr(self.parent, self.method_name)  # type: ignore
        return method(value)

    def to_internal_value(self, data):
        return {self.field_name: data}


class BaseArchiveDetailSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField("get_files_for_archive")
    cdn_base_url = serializers.SerializerMethodField("get_cdn_base_url")

    def get_cdn_base_url(self, instance) -> str:
        """
        Generate the url for where to find the "blob" files of the package.
        This url points to the extracted version of the archive hosted at the CDN server.
        """
        return f"{settings.ASKANNA_CDN_URL}/files/blob/{instance.uuid}"

    def get_files_for_archive(self, instance) -> list[dict[str, str | int]]:
        """
        On the fly reading a zip archive and returns the information about what files are in the archive
        """
        return get_files_and_directories_in_zip_file(instance.stored_path)
