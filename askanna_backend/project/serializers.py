from rest_framework import serializers

from project.models import Project
from users.models import Membership, MSP_WORKSPACE
from workspace.models import Workspace


class ProjectSerializer(serializers.ModelSerializer):
    created_by = serializers.SerializerMethodField("get_created_by")
    workspace = serializers.SerializerMethodField("get_workspace")

    def get_workspace(self, instance):
        return {
            "uuid": instance.workspace.uuid,
            "short_uuid": instance.workspace.short_uuid,
            "name": instance.workspace.uuid,
        }

    def get_created_by(self, instance):
        if instance.created_by is not None:
            return {
                "uuid": instance.created_by.uuid,
                "short_uuid": instance.created_by.short_uuid,
                "name": instance.created_by.get_name(),
            }
        return {
            "uuid": None,
            "short_uuid": None,
            "name": None,
        }

    class Meta:
        model = Project
        exclude = [
            "deleted",
            "activate_date",
            "deactivate_date",
        ]


class ProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ["name", "description"]

    def update(self, instance, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.save()
        return instance


class ProjectCreateSerializer(serializers.ModelSerializer):
    workspace = serializers.CharField(max_length=19)

    class Meta:
        model = Project
        fields = ["name", "workspace", "description"]

    def create(self, validated_data):
        validated_data.update(**{"created_by": self.context["request"].user})
        return super().create(validated_data)

    def validate_workspace(self, value):
        """
        Validation of a given workspace short_uuid

        Steps needed:
        - check in database for exisiting workspace with short_uuid
        - check whether the user is a member of this workspace
        - return the workspace.uuid instead of short_uuid in `value`

        In all cases of error, return a message that workspace doesn't exist or user has no access

        """
        try:
            workspace = Workspace.objects.get(short_uuid=value)
        except Exception as e:
            print(e)
            raise serializers.ValidationError(
                "Workspace with SUUID={} was not found".format(value)
            )
        else:
            # check whether the user has access to this workspace

            is_member = (
                self.context["request"]
                .user.memberships.filter(
                    object_type=MSP_WORKSPACE, object_uuid=workspace.uuid
                )
                .count()
                > 0
            )
            if is_member:
                return workspace
            else:
                raise serializers.ValidationError(
                    "User is not member of workspace {}".format(value)
                )

        return value

    def to_representation(self, instance):
        request = self.context["request"]
        url = "{scheme}://{host}/{workspace}/project/{project}".format(
            scheme=request.scheme,
            host=request.get_host().replace("-api", "").replace("api", ""),
            workspace=instance.workspace.short_uuid,
            project=instance.short_uuid,
        )
        return {
            "uuid": instance.uuid,
            "short_uuid": instance.short_uuid,
            "name": instance.name,
            "description": instance.description,
            "workspace": {
                "uuid": instance.workspace.uuid,
                "short_uuid": instance.workspace.short_uuid,
                "name": instance.workspace.uuid,
            },
            "created_by": {
                "uuid": instance.created_by.uuid,
                "short_uuid": instance.created_by.short_uuid,
                "name": instance.created_by.get_name(),
            },
            "status": 1,
            "created": instance.created,
            "modified": instance.modified,
            "url": url,
        }
