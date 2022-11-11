from core.serializers import BaseArchiveDetailSerializer
from django.core.exceptions import ObjectDoesNotExist
from package.models import ChunkedPackagePart, Package
from project.models import Project
from rest_framework import serializers
from users.models import MSP_WORKSPACE


class PackageCreateSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(max_length=256)
    project = serializers.CharField(max_length=19)

    class Meta:
        model = Package
        exclude = ["uuid"]

    def create(self, validated_data):
        validated_data["created_by"] = self.context.get("request").user
        original_filename = validated_data.get("filename")
        del validated_data["filename"]
        validated_data.update(**{"original_filename": original_filename})
        return super().create(validated_data)

    def validate_project(self, value):
        """
        Validation of the project specified in the create request
        """
        try:
            project = Project.objects.get(suuid=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(f"Project with SUUID={value} was not found")
        else:
            # check whether the user has access to this projet
            request = self.context["request"]
            member_of_workspaces = request.user.memberships.filter(
                object_type=MSP_WORKSPACE,
                deleted__isnull=True,
            ).values_list("object_uuid", flat=True)

            is_member = project.workspace.uuid in member_of_workspaces
            if is_member:
                return project
            else:
                raise serializers.ValidationError(f"User has no access to project with SUUID={value}")

        return value


class PackageSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")
    workspace = serializers.SerializerMethodField("get_workspace")
    project = serializers.SerializerMethodField("get_project")
    filename = serializers.SerializerMethodField("get_filename")

    def get_created_by(self, instance):
        if instance.member:
            return instance.member.relation_to_json
        elif instance.created_by:
            return instance.created_by.relation_to_json
        else:
            return None

    def get_workspace(self, instance):
        return instance.project.workspace.relation_to_json

    def get_project(self, instance):
        return instance.project.relation_to_json

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible
        on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    class Meta:
        model = Package
        fields = [
            "suuid",
            "workspace",
            "project",
            "created_by",
            "created",
            "modified",
            "name",
            "description",
            "filename",
            "size",
        ]


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"


class PackageSerializerDetail(BaseArchiveDetailSerializer):
    filename = serializers.SerializerMethodField("get_filename")
    project = serializers.SerializerMethodField("get_project")
    workspace = serializers.SerializerMethodField("get_workspace")
    created_by = serializers.SerializerMethodField("get_created_by")

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible
        on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    def get_created_by(self, instance):
        if instance.member:
            return instance.member.relation_to_json
        elif instance.created_by:
            return instance.get_created_by()
        else:
            return None

    def get_workspace(self, instance):
        return instance.project.workspace.relation_to_json

    def get_project(self, instance):
        return instance.project.relation_to_json

    class Meta:
        model = Package
        exclude = ["uuid", "original_filename", "deleted", "finished", "member"]
