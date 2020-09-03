import base64
from rest_framework import serializers

from job.models import (
    JobDef,
    JobRun,
    JobPayload,
    JobArtifact,
    ChunkedArtifactPart,
    ChunkedJobOutputPart,
    JobOutput,
    JobVariable,
)


class JobOutputSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOutput
        fields = "__all__"


class JobSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        return str(instance.project.uuid)

    class Meta:
        model = JobDef
        fields = "__all__"


class StartJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = "__all__"


class JobPayloadSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")

    def get_project(self, instance):
        return str(instance.jobdef.uuid)

    class Meta:
        model = JobPayload
        fields = "__all__"


class JobRunSerializer(serializers.ModelSerializer):
    package = serializers.SerializerMethodField("get_package")
    version = serializers.SerializerMethodField("get_version")
    project = serializers.SerializerMethodField("get_project")
    owner = serializers.SerializerMethodField("get_user")
    trigger = serializers.SerializerMethodField("get_user")
    runner = serializers.SerializerMethodField("get_runner")
    jobid = serializers.SerializerMethodField("get_jobid")

    payload = serializers.SerializerMethodField("get_payload")

    jobdef = serializers.SerializerMethodField("get_jobdef")

    def get_payload(self, instance):
        payload = JobPayloadSerializer(instance.payload, many=False)
        return payload.data

    def get_jobdef(self, instance):
        jobdef = instance.jobdef
        return {
            "name": jobdef.name,
            "uuid": jobdef.uuid,
            "short_uuid": jobdef.short_uuid,
        }

    def get_jobid(self, instance):
        # FIXME: this is to fix empty jobids from unran Celery jobs
        return instance.jobid

    def get_runner(self, instance):
        # FIXME: replace with actual values
        return {
            "name": "Python 3.7",
            "uuid": "",
            "short_uuid": "1234-5678-9012-3456",
            "cpu_time": (instance.modified - instance.created).seconds,
            "cpu_cores": 1,
            "memory_mib": 70,
            "job_status": 0,
        }

    def get_trigger(self, instance):
        # FIXME: return the real trigger source
        return "API"

    def get_version(self, instance):
        # FIXME: replace with actual version information
        # stick version to the package version
        return {
            "name": "latest",
            "uuid": "",
            "short_uuid": "2222-3333-2222-2222",
        }

    def get_package(self, instance):
        # FIXME: replace with actual data after models refactor
        package = instance.package
        if package:
            return {
                "name": package.filename,
                "uuid": package.uuid,
                "short_uuid": package.short_uuid,
            }
        return {"name": "latest", "uuid": None, "short_uuid": None}

    def get_project(self, instance):
        project = instance.jobdef.project
        return {
            "name": project.name,
            "uuid": project.uuid,
            "short_uuid": project.short_uuid,
        }

    def get_user(self, instance):
        if instance.owner:
            return {
                "name": instance.owner.get_name(),
                "uuid": instance.owner.uuid,
                "short_uuid": instance.owner.short_uuid,
            }
        return {
            "name": None,
            "uuid": None,
            "short_uuid": None,
        }

    class Meta:
        model = JobRun
        fields = "__all__"


class JobArtifactSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField("get_project")
    # jobrun = serializers.SerializerMethodField('get_jobrun')

    def get_project(self, instance):
        project = instance.jobrun.jobdef.project
        return {
            "name": project.name,
            "uuid": project.uuid,
            "short_uuid": project.short_uuid,
        }

    def get_jobrun(self, instance):
        jobrun = instance.jobrun
        return {
            "name": jobrun.name,
            "uuid": jobrun.uuid,
            "short_uuid": jobrun.short_uuid,
        }

    class Meta:
        model = JobArtifact
        fields = "__all__"


class JobArtifactSerializerForInsert(serializers.ModelSerializer):
    class Meta:
        model = JobArtifact
        fields = "__all__"


class ChunkedArtifactPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedArtifactPart
        fields = "__all__"


class ChunkedJobOutputPartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedJobOutputPart
        fields = "__all__"


class JobVariableSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField("get_value")

    def get_value(self, instance):
        # if 'Authorization' in self.context['request'].headers.keys():
        #     # extract the token
        #     raw_token = self.context['request'].headers.get('Authorization')
        #     token = raw_token.split(' ')[1]
        #     return base64.b64encode('{}{}'.format(token, instance.value).encode('utf-8'))
        return instance.value

    class Meta:
        model = JobVariable
        # fields = "__all__"
        exclude = [
            "deleted",
            "project",
        ]


class JobVariableUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobVariable
        fields = ["value"]

    def update(self, instance, validated_data):
        instance.value = validated_data.get("value", instance.value)
        instance.save()
        return instance

    def validate_value(self, value):
        """
        Validation of a given new value for value
        """
        return value

    def to_representation(self, instance):
        return {
            'uuid': instance.uuid,
            'short_uuid': instance.short_uuid,
            'name': instance.name,
            'value': instance.value,
            'created': instance.created,
            'modified': instance.modified,
            'status': 1,
            "message": "Successfully changed the variable",
        }