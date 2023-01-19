from core.serializers import BaseArchiveDetailSerializer
from package.models import Package
from project.models import Project
from project.serializers import ProjectRelationSerializer
from rest_framework import serializers
from users.serializers.people import MembershipRelationSerializer
from workspace.serializers import WorkspaceRelationSerializer


class PackageSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(source="original_filename")
    workspace = WorkspaceRelationSerializer(read_only=True, source="project.workspace")
    project = ProjectRelationSerializer(read_only=True)
    created_by = MembershipRelationSerializer(read_only=True, source="member")

    class Meta:
        model = Package
        fields = [
            "suuid",
            "filename",
            "size",
            "name",
            "description",
            "workspace",
            "project",
            "created_by",
            "created",
            "modified",
        ]


class PackageSerializerWithFileList(PackageSerializer, BaseArchiveDetailSerializer):
    class Meta:
        model = Package
        fields = [
            "suuid",
            "filename",
            "size",
            "name",
            "description",
            "workspace",
            "project",
            "created_by",
            "created",
            "modified",
            "cdn_base_url",
            "files",
        ]


class PackageCreateSerializer(PackageSerializer):
    project_suuid = serializers.SlugRelatedField(
        slug_field="suuid",
        write_only=True,
        required=True,
        queryset=Project.objects.active(),
        source="project",
    )

    def create(self, validated_data):
        validated_data["created_by"] = self.context.get("request").user
        return super().create(validated_data)

    class Meta(PackageSerializer.Meta):
        fields = PackageSerializer.Meta.fields + ["project_suuid"]
