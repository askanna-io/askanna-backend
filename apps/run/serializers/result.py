from django.utils import timezone
from rest_framework import serializers

from account.models import Membership
from core.serializers import RelationSerializer
from storage.models import File
from storage.serializers import FileDownloadInfoSerializer, FileUploadInfoSerializer
from storage.utils.file import get_content_type_from_file, get_md5_from_file


class RunResultCreateBaseSerializer(serializers.Serializer):
    run = RelationSerializer(read_only=True, source="*")

    result = serializers.FileField(write_only=True, required=False)

    download_info = FileDownloadInfoSerializer(read_only=True, source="result_file")
    upload_info = FileUploadInfoSerializer(read_only=True, source="result_file")

    filename = serializers.CharField(required=False, source="result_file_info.filename")
    size = serializers.IntegerField(
        required=False, help_text="Size of the file in bytes", source="result_file_info.size"
    )
    etag = serializers.CharField(required=False, help_text="MD5 digest of the file", source="result_file_info.etag")
    content_type = serializers.CharField(
        required=False, source="result_file_info.content_type", help_text="Content type of the file"
    )

    def create(self, validated_data):
        run = self.context["run"]

        result_file = validated_data.pop("result", None)
        result_file_info = validated_data.pop("result_file_info", {})

        file_name = result_file_info.get("filename") or (result_file and result_file.name) or ""
        file_size = result_file_info.get("size") or (result_file and result_file.size) or None
        file_etag = result_file_info.get("etag") or (result_file and get_md5_from_file(result_file)) or ""
        file_content_type = (
            result_file_info.get("content_type") or (result_file and get_content_type_from_file(result_file)) or ""
        )

        file = File.objects.create(
            name=file_name,
            description=result_file_info.get("description", ""),
            file=result_file,
            size=file_size,
            etag=file_etag,
            content_type=file_content_type,
            upload_to=run.upload_result_directory,
            created_for=run,
            created_by=Membership.objects.get_workspace_membership(
                user=self.context["request"].user, workspace=run.workspace
            ),
            completed_at=timezone.now() if result_file else None,
        )

        run.result = file
        run.save()
        run.refresh_from_db()

        run.result_file_info = {
            "filename": file_name,
            "size": file_size,
            "etag": file_etag,
            "content_type": file_content_type,
        }
        run.result_file = file

        return run

    class Meta:
        fields = [
            "run",
            "result",
            "filename",
            "size",
            "etag",
            "content_type",
        ]


class RunResultCreateWithFileSerializer(RunResultCreateBaseSerializer):
    result = serializers.FileField(write_only=True, required=True)

    upload_info = None

    def validate_size(self, value):
        size = self.initial_data["result"].size
        if value != size:
            raise serializers.ValidationError(f"Size '{value}' does not match the size of the received file '{size}'.")

        return value

    def validate_etag(self, value):
        md5_digest = get_md5_from_file(self.initial_data["result"])
        if value != md5_digest:
            raise serializers.ValidationError(
                f"ETag '{value}' does not match the ETag of the received file '{md5_digest}'."
            )

        return value

    def validate_content_type(self, value):
        content_type = get_content_type_from_file(self.initial_data["result"])
        if value != content_type:
            raise serializers.ValidationError(
                f"Content type '{value}' does not match the content type of the received file '{content_type}'."
            )

        return value


class RunResultCreateWithoutFileSerializer(RunResultCreateBaseSerializer):
    filename = serializers.CharField(required=True, source="result_file_info.filename")

    result = None
    download_info = None
