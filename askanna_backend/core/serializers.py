from core.utils import get_files_and_directories_in_zip_file
from django.conf import settings
from rest_framework import serializers


class BaseArchiveDetailSerializer(serializers.ModelSerializer):
    files = serializers.SerializerMethodField("get_files_for_archive")
    cdn_base_url = serializers.SerializerMethodField("get_base_url")

    def get_base_url(self, instance):
        """
        Generate the url for where to find the "blob" files of the package.
        This url points to the extracted version of the archive hosted at the CDN server.
        Please note the /files/blob/ prefix
        """
        return "{BASE_URL}/files/blob/{LOCATION}".format(BASE_URL=settings.ASKANNA_CDN_URL, LOCATION=instance.uuid)

    def get_files_for_archive(self, instance):
        """
        On the fly reading a zip archive and returns the information about what files are in the archive
        """
        return get_files_and_directories_in_zip_file(instance.stored_path)
