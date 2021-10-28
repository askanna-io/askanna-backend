from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from core.serializers import BaseArchiveDetailSerializer
from package.models import Package, ChunkedPackagePart
from project.models import Project
from users.models import MSP_WORKSPACE


class PackageCreateSerializer(serializers.ModelSerializer):
    filename = serializers.CharField(max_length=256)
    project = serializers.CharField(max_length=19)

    class Meta:
        model = Package
        # fields = ["filename", "project", "size", "description"]
        fields = "__all__"

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
            project = Project.objects.get(short_uuid=value)
        except ObjectDoesNotExist:
            raise serializers.ValidationError(
                f"Project with SUUID={value} was not found"
            )
        else:
            # check whether the user has access to this projet
            request = self.context["request"]
            member_of_workspaces = request.user.memberships.filter(
                object_type=MSP_WORKSPACE
            ).values_list("object_uuid", flat=True)

            is_member = project.workspace.uuid in member_of_workspaces
            if is_member:
                return project
            else:
                raise serializers.ValidationError(
                    f"User has no access to project with SUUID={value}"
                )

        return value


class PackageSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")

    def get_created_by(self, instance):
        user = instance.created_by
        member = instance.member
        if member:
            return member.relation_to_json
        if user:
            return user.relation_to_json

        # if not of the user or member is filled, return default empty
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

    filename = serializers.SerializerMethodField("get_filename")

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible
        on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    class Meta:
        model = Package
        fields = "__all__"


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"


class PackageSerializerDetail(BaseArchiveDetailSerializer):

    filename = serializers.SerializerMethodField("get_filename")

    def get_filename(self, instance):
        """
        The filename is stored in another property field which is only accesible
        on the instance level, not on databaselevel
        """
        filename = instance.original_filename
        return filename

    class Meta:
        model = Package
        exclude = ("original_filename", "deleted")
