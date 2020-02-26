from rest_framework import serializers

from job.models import JobDef, JobRun, JobPayload


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = (
            'id',
            'uuid',
            'name',
            'status',
        )


class JobRunTestSerializer(serializers.BaseSerializer):
    """
    Possible serialization implementation for the JobRun objects associated
    with a specified JobDef.

    In our Job concept, there is always an associated JobDef. When we make
    use of the Job.runs() method (notice the plural), we want to return
    all the jobrun objects associated with the specified JobDef.

    We can use the DRF serializers to achieve this result.

    Currently in use in the job.view_actions:JobActionView.runs() method
    implementation.

    See example in: https://www.django-rest-framework.org/api-guide/serializers/#baseserializer
    on how to use.

    FIXME:
        - currently we are not checking pagination and take into account the
          number of JobRuns for a particular JobDef. It can be a large
          number, so it's better if we paginate this.
    """
    def to_representation(self, instance):
        jobpayload = JobPayload.objects.get(uuid=instance.payload)
        return {
            'uuid': instance.uuid,
            'payload': jobpayload.payload,
            'status': instance.status,
            'runtime': instance.runtime,
            'memory': instance.memory,
            'return_payload': instance.output.return_payload,
            'stdout': instance.output.stdout,
            'created': instance.created,
            'finished': instance.output.created
        }
