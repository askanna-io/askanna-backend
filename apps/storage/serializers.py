from pathlib import Path
from tempfile import SpooledTemporaryFile

from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import serializers

from core.serializers import RelationSerializer
from storage.file import MultipartFile
from storage.models import File
from storage.utils.file import get_md5_from_file


class FileUploadURLField(serializers.HyperlinkedIdentityField):
    view_name = "storage-file-upload-part"
    lookup_field = "suuid"

    def __init__(self, *args, **kwargs):
        kwargs["view_name"] = self.view_name
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        representation_value = super().to_representation(value)
        return representation_value[: -len("part/")]


class FileDownloadInfoSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="storage-file-download", lookup_field="suuid")
    type = serializers.SerializerMethodField(help_text="The type of service that handles the download")

    def get_type(self, obj) -> str:
        return "askanna"

    class Meta:
        model = File
        fields = [
            "type",
            "url",
        ]


class FilelistFileInfoSerializer(serializers.Serializer):
    path = serializers.CharField(read_only=True)
    parent = serializers.CharField(read_only=True)
    name = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    type = serializers.CharField(read_only=True)
    last_modified = serializers.DateTimeField(read_only=True)


class FileInfoSerializer(serializers.ModelSerializer):
    filename = serializers.SerializerMethodField(read_only=True)
    size = serializers.IntegerField(read_only=True)
    etag = serializers.CharField(read_only=True)
    content_type = serializers.CharField(read_only=True)
    download_info = FileDownloadInfoSerializer(source="*", read_only=True)
    created_for = RelationSerializer(read_only=True)
    created_by = RelationSerializer(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True)

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
            "size",
            "etag",
            "content_type",
            "download_info",
            "created_for",
            "created_by",
            "created_at",
            "modified_at",
            "completed_at",
        ]


class FileUploadInfoSerializer(serializers.ModelSerializer):
    url = FileUploadURLField(read_only=True)
    type = serializers.SerializerMethodField(help_text="The type of service that handles the upload")

    def get_type(self, obj) -> str:
        return "askanna"

    class Meta:
        model = File
        fields = [
            "type",
            "url",
        ]


class FilePartSerializer(serializers.Serializer):
    part_number = serializers.IntegerField(required=True, min_value=1)
    etag = serializers.CharField(required=False, help_text="MD5 digest of the file part")


class FileUploadPartSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    part = serializers.FileField(required=True, write_only=True)
    part_number = serializers.IntegerField(required=True, min_value=1, max_value=10000)
    etag = serializers.CharField(required=False, help_text="MD5 digest of the file part")

    def validate_etag(self, value):
        part_etag = get_md5_from_file(self.initial_data["part"])

        if value != part_etag:
            raise serializers.ValidationError(
                f"ETag '{value}' is not equal to the ETag of the part received '{part_etag}'"
            )

        return value

    def save_part(self):
        part_data = self.validated_data["part"]

        self.instance.part_number = self.validated_data["part_number"]
        self.instance.size = part_data.size
        self.instance.etag = self.validated_data.get("etag", None) or get_md5_from_file(part_data)

        # Use the Storage system to save the file. For the name of the file we use the part number.
        # We make sure to delete the old file first and then save the new file.
        part_name = self.instance.get_upload_to_part_name(self.instance.part_number)
        self.instance.file.storage.delete(part_name)
        saved_name = self.instance.file.storage.save(name=part_name, content=part_data)

        # To make sure the file is saved correctly, we check the name of the file with the name that is returned
        # after saving the file. If the names are not equal, then we raise an error and remove the file.
        if part_name != saved_name:
            self.instance.file.storage.delete(saved_name)
            raise serializers.ValidationError(
                {"detail": f"Something went wrong while saving part '{self.instance.part_number}'."}
            )

    class Meta:
        model = File
        fields = [
            "suuid",
            "part",
            "part_number",
            "etag",
        ]


class FileUploadCompleteSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)
    parts = serializers.ListField(child=FilePartSerializer(), required=False, write_only=True)
    etag = serializers.CharField(required=False, help_text="MD5 digest of the file")

    def validate_parts(self, value):
        instance: File = self.instance

        if len(instance.part_filenames) != len(value):
            raise serializers.ValidationError(
                f"Expected {len(instance.part_filenames)} parts, but received {len(value)} parts"
            )

        for part in value:
            part_number = part.get("part_number")

            part_name = instance.get_upload_to_part_name(part_number)
            if not instance.file.storage.exists(part_name):
                raise serializers.ValidationError(f"Part {part_number} does not exist in the storage system")

            etag = part.get("etag")
            if etag:
                with instance.file.storage.open(part_name) as file:
                    part_etag = get_md5_from_file(file)
                if etag != part_etag:
                    raise serializers.ValidationError(
                        f"ETag '{etag}' for part {part_number} is not equal to the ETag '{part_etag}' of "
                        "the file part received."
                    )

        return value

    def complete_upload(self):
        instance: File = self.instance
        update_fields = ["file"]

        if self.instance.file.storage.support_chunks:
            instance.file.save(name=instance.name, content=MultipartFile(instance.file))
        else:
            with SpooledTemporaryFile(max_size=settings.FILE_MAX_MEMORY_SIZE, suffix=".StorageFile") as tmp_file:
                for part_filename in instance.part_filenames:
                    part_file = instance.upload_to + "/" + part_filename
                    with instance.file.storage.open(part_file) as file:
                        tmp_file.write(file.read())

                tmp_file.seek(0)

                instance.file.save(
                    name=instance.name,
                    content=ContentFile(name=instance.name, content=tmp_file.read()),
                )

        with instance.file.open() as file:
            file_etag = get_md5_from_file(file)

        if instance.etag and instance.etag != file_etag:
            instance.file.delete()
            raise serializers.ValidationError(
                {"etag": f"ETag '{instance.etag}' is not equal to the ETag '{file_etag}' of the file received."}
            )
        if not instance.etag:
            instance.etag = file_etag
            update_fields.append("etag")

        # If complete request contains an ETag, then we check if the ETag is equal to the ETag of the file.
        if (
            isinstance(self.validated_data, dict)
            and self.validated_data.get("etag", None)
            and self.validated_data["etag"] != instance.etag
        ):
            instance.file.delete()
            raise serializers.ValidationError(
                {
                    "etag": f"ETag '{self.validated_data['etag']}' is not equal to the ETag '{instance.etag}' of "
                    "the file received."
                }
            )

        file_size = instance.file.size
        if instance.size and instance.size != file_size:
            instance.file.delete()
            raise serializers.ValidationError(
                {"size": f"Size '{instance.size}' is not equal to the size '{file_size}' of the file received."}
            )
        if not instance.size:
            instance.size = file_size
            update_fields.append("size")

        file_content_type = instance.file.file.content_type
        if instance.content_type and instance.content_type != file_content_type:
            instance.file.delete()
            raise serializers.ValidationError(
                {
                    "content_type": f"Content type '{instance.content_type}' is not equal to the content type "
                    f"'{file_content_type}' of the file received."
                }
            )
        if not instance.content_type:
            instance.content_type = file_content_type
            update_fields.append("content_type")

        instance.completed_at = timezone.now()
        update_fields.extend(["completed_at", "modified_at"])

        instance.save(update_fields=update_fields)

        instance.delete_parts()

    class Meta:
        model = File
        fields = [
            "suuid",
            "parts",
            "etag",
        ]
