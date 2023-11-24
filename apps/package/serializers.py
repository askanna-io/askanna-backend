from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from account.models import Membership
from account.serializers.membership import MembershipRelationSerializer
from core.serializers import RelationSerializer
from core.utils import get_files_and_directories_in_zip_file
from package.models import Package
from project.models import Project
from storage.models import File
from storage.serializers import FileDownloadInfoSerializer, FileUploadInfoSerializer
from storage.utils import get_content_type_from_file, get_md5_from_file


class PackageSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)

    filename = serializers.CharField(read_only=True, source="package_file.name")
    size = serializers.IntegerField(read_only=True, source="package_file.size")
    etag = serializers.CharField(read_only=True, source="package_file.etag", help_text="MD5 digest of the file")
    content_type = serializers.CharField(
        read_only=True,
        source="package_file.content_type",
        help_text="Content type of the file. For packages only zip files are allowed.",
    )

    description = serializers.CharField(default="", source="package_file.description")

    download_info = FileDownloadInfoSerializer(read_only=True, source="package_file")

    created_by = MembershipRelationSerializer(read_only=True, source="package_file.created_by")

    project = RelationSerializer(read_only=True)
    workspace = RelationSerializer(read_only=True, source="project.workspace")

    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, default=None, source="package_file.completed_at")

    def update(self, instance, validated_data):
        package_file = validated_data.pop("package_file", {})
        if package_file and "description" in package_file.keys():
            instance.package_file.description = package_file.get("description", "")
            instance.package_file.save()

        instance.refresh_from_db()
        return instance

    class Meta:
        model = Package
        fields = [
            "suuid",
            "filename",
            "size",
            "etag",
            "content_type",
            "description",
            "download_info",
            "created_by",
            "project",
            "workspace",
            "created_at",
            "modified_at",
            "completed_at",
        ]


class PackageSerializerWithFileList(PackageSerializer):
    files = serializers.SerializerMethodField("get_files_for_archive", read_only=True)

    def get_files_for_archive(self, instance) -> list[dict[str, str | int]]:
        """On the fly reading a zip archive and returns the information about what files are in the archive"""
        return get_files_and_directories_in_zip_file(instance.package_file.file)

    class Meta(PackageSerializer.Meta):
        fields = PackageSerializer.Meta.fields + ["files"]


class PackageCreateBaseSerializer(PackageSerializer):
    project_suuid = serializers.SlugRelatedField(
        slug_field="suuid",
        write_only=True,
        required=True,
        queryset=Project.objects.active(add_select_related=True),
        source="project",
    )

    package = serializers.FileField(write_only=True, required=False)

    filename = serializers.CharField(required=False, source="package_file.name")
    size = serializers.IntegerField(required=False, source="package_file.size")
    etag = serializers.CharField(required=False, source="package_file.etag", help_text="MD5 digest of the file")

    description = serializers.CharField(required=False, source="package_file.description")

    def create(self, validated_data):
        package_file = validated_data.pop("package", None)
        package_file_info = validated_data.pop("package_file", {})

        instance = super().create(validated_data)

        file_name = package_file_info.get("name") or (package_file and package_file.name) or ""
        file_size = package_file_info.get("size") or (package_file and package_file.size) or None
        file_etag = package_file_info.get("etag") or (package_file and get_md5_from_file(package_file)) or ""

        file = File.objects.create(
            name=file_name,
            description=package_file_info.get("description", ""),
            file=package_file,
            size=file_size,
            etag=file_etag,
            content_type="application/zip",
            created_for=instance,
            created_by=Membership.objects.get_workspace_membership(
                user=self.context.get("request").user, workspace=instance.project.workspace
            ),
            completed_at=timezone.make_aware(datetime.now()) if package_file else None,
        )

        instance.package_file = file
        instance.save()
        instance.refresh_from_db()

        if package_file:
            instance.extract_jobs_from_askanna_config()

        return instance

    class Meta(PackageSerializer.Meta):
        fields = ["project_suuid", "package"] + PackageSerializer.Meta.fields


class PackageCreateWithFileSerializer(PackageCreateBaseSerializer):
    package = serializers.FileField(write_only=True, required=True)

    def validate_size(self, value):
        size = self.initial_data["package"].size
        if value != size:
            raise serializers.ValidationError(f"Size '{value}' does not match the size of the received file '{size}'.")

        return value

    def validate_etag(self, value):
        md5_digest = get_md5_from_file(self.initial_data["package"])
        if value != md5_digest:
            raise serializers.ValidationError(
                f"ETag '{value}' does not match the ETag of the received file '{md5_digest}'."
            )

        return value

    def validate_package(self, value):
        if get_content_type_from_file(value) != "application/zip":
            raise serializers.ValidationError("Only zip files are allowed for packages")

        return value


class PackageCreateWithoutFileSerializer(PackageCreateBaseSerializer):
    filename = serializers.CharField(required=True, source="package_file.name")
    upload_info = FileUploadInfoSerializer(read_only=True, source="package_file")

    package = None
    download_info = None

    class Meta(PackageCreateBaseSerializer.Meta):
        fields = [
            "project_suuid",
            "suuid",
            "upload_info",
            "filename",
            "size",
            "etag",
            "content_type",
            "description",
            "created_by",
            "project",
            "workspace",
            "created_at",
            "modified_at",
            "completed_at",
        ]
