from django.utils import timezone
from rest_framework import serializers

from account.models import Membership
from account.serializers.membership import MembershipRelationSerializer
from core.models import ObjectReference
from core.serializers import RelationSerializer
from run.models import Run, RunArtifact
from storage.models import File
from storage.serializers import (
    FileDownloadInfoSerializer,
    FilelistFileInfoSerializer,
    FileUploadInfoSerializer,
)
from storage.utils.file import get_content_type_from_file, get_md5_from_file


class ArtifactRelationSerializer(serializers.ModelSerializer):
    relation = serializers.CharField(read_only=True, default="artifact")
    suuid = serializers.CharField(read_only=True)
    size = serializers.IntegerField(read_only=True, source="artifact_file.size")
    count_dir = serializers.IntegerField(read_only=True, source="artifact_file.count_dir_from_zipfile")
    count_files = serializers.IntegerField(read_only=True, source="artifact_file.count_files_from_zipfile")

    class Meta:
        model = RunArtifact
        fields = [
            "relation",
            "suuid",
            "size",
            "count_dir",
            "count_files",
        ]


class RunArtifactSerializer(serializers.ModelSerializer):
    suuid = serializers.CharField(read_only=True)

    filename = serializers.CharField(read_only=True, source="artifact_file.name")
    size = serializers.IntegerField(read_only=True, source="artifact_file.size")
    etag = serializers.CharField(read_only=True, source="artifact_file.etag", help_text="MD5 digest of the file")
    content_type = serializers.CharField(
        read_only=True,
        source="artifact_file.content_type",
        help_text="Content type of the file. For artifacts only zip files are allowed.",
    )
    count_dir = serializers.IntegerField(read_only=True, source="artifact_file.count_dir_from_zipfile")
    count_files = serializers.IntegerField(read_only=True, source="artifact_file.count_files_from_zipfile")

    description = serializers.CharField(
        required=False, default="", allow_blank=True, source="artifact_file.description"
    )

    download_info = FileDownloadInfoSerializer(read_only=True, source="artifact_file")

    created_by = MembershipRelationSerializer(read_only=True, source="artifact_file.created_by")

    run = RelationSerializer(read_only=True)
    job = RelationSerializer(read_only=True, source="run.jobdef")
    project = RelationSerializer(read_only=True, source="run.jobdef.project")
    workspace = RelationSerializer(read_only=True, source="run.jobdef.project.workspace")

    created_at = serializers.DateTimeField(read_only=True)
    modified_at = serializers.DateTimeField(read_only=True)
    completed_at = serializers.DateTimeField(read_only=True, default=None, source="artifact_file.completed_at")

    def update(self, instance, validated_data):
        artifact_file = validated_data.pop("artifact_file", {})
        if artifact_file and "description" in artifact_file.keys():
            instance.artifact_file.description = artifact_file.get("description", "")
            instance.artifact_file.save()

        instance.refresh_from_db()
        return instance

    class Meta:
        model = RunArtifact
        fields = [
            "suuid",
            "filename",
            "size",
            "etag",
            "content_type",
            "count_dir",
            "count_files",
            "description",
            "download_info",
            "created_by",
            "run",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
            "completed_at",
        ]


class RunArtifactSerializerWithFileList(RunArtifactSerializer):
    files = serializers.ListField(
        read_only=True, child=FilelistFileInfoSerializer(), source="artifact_file.files_and_directories_in_zipfile"
    )

    class Meta(RunArtifactSerializer.Meta):
        fields = RunArtifactSerializer.Meta.fields + ["files"]


class RunArtifactCreateBaseSerializer(RunArtifactSerializer):
    run_suuid = serializers.SlugRelatedField(
        slug_field="suuid",
        write_only=True,
        required=True,
        queryset=Run.objects.active(add_select_related=True),
        source="run",
    )

    artifact = serializers.FileField(write_only=True, required=False)

    filename = serializers.CharField(required=False, source="artifact_file.name")
    size = serializers.IntegerField(required=False, source="artifact_file.size")
    etag = serializers.CharField(required=False, source="artifact_file.etag", help_text="MD5 digest of the file")

    def create(self, validated_data):
        artifact_file = validated_data.pop("artifact", None)
        artifact_file_info = validated_data.pop("artifact_file", {})

        instance = super().create(validated_data)

        file_name = artifact_file_info.get("name") or (artifact_file and artifact_file.name) or ""
        file_size = artifact_file_info.get("size") or (artifact_file and artifact_file.size) or None
        file_etag = artifact_file_info.get("etag") or (artifact_file and get_md5_from_file(artifact_file)) or ""

        ObjectReference.objects.create(run_artifact=instance)

        file = File.objects.create(
            name=file_name,
            description=artifact_file_info.get("description", ""),
            file=artifact_file,
            size=file_size,
            etag=file_etag,
            content_type="application/zip",
            created_for=instance,
            created_by=Membership.objects.get_workspace_membership(
                user=self.context.get("request").user, workspace=instance.run.jobdef.project.workspace
            ),
            completed_at=timezone.now() if artifact_file else None,
        )

        instance.artifact_file = file
        instance.save()
        instance.refresh_from_db()

        return instance

    class Meta(RunArtifactSerializer.Meta):
        fields = ["run_suuid", "artifact"] + RunArtifactSerializer.Meta.fields


class RunArtifactCreateWithFileSerializer(RunArtifactCreateBaseSerializer):
    artifact = serializers.FileField(write_only=True, required=True)

    def validate_size(self, value):
        size = self.initial_data["artifact"].size
        if value != size:
            raise serializers.ValidationError(f"Size '{value}' does not match the size of the received file '{size}'.")

        return value

    def validate_etag(self, value):
        md5_digest = get_md5_from_file(self.initial_data["artifact"])
        if value != md5_digest:
            raise serializers.ValidationError(
                f"ETag '{value}' does not match the ETag of the received file '{md5_digest}'."
            )

        return value

    def validate_artifact(self, value):
        if get_content_type_from_file(value) != "application/zip":
            raise serializers.ValidationError("Only zip files are allowed for artifacts")

        return value


class RunArtifactCreateWithoutFileSerializer(RunArtifactCreateBaseSerializer):
    upload_info = FileUploadInfoSerializer(read_only=True, source="artifact_file")

    filename = serializers.CharField(required=True, source="artifact_file.name")

    artifact = None
    download_info = None

    class Meta(RunArtifactCreateBaseSerializer.Meta):
        fields = [
            "run_suuid",
            "suuid",
            "upload_info",
            "filename",
            "size",
            "etag",
            "content_type",
            "description",
            "created_by",
            "run",
            "job",
            "project",
            "workspace",
            "created_at",
            "modified_at",
            "completed_at",
        ]
