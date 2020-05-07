from rest_framework import serializers

from job.models import JobDef, JobRun, JobPayload


class JobSerializer(serializers.ModelSerializer):
    project = serializers.SerializerMethodField('get_project')

    def get_project(self, instance):
        return str(instance.project.uuid)
    class Meta:
        model = JobDef
        fields = "__all__"

class StartJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = '__all__'

class JobPayloadSerializer(serializers.ModelSerializer):

    project = serializers.SerializerMethodField('get_project')

    def get_project(self, instance):
        return str(instance.jobdef.uuid)

    class Meta:
        model = JobPayload
        fields = '__all__'

class JobRunSerializer(serializers.ModelSerializer):
    package = serializers.SerializerMethodField("get_package")
    version = serializers.SerializerMethodField("get_version")
    project = serializers.SerializerMethodField("get_project")
    owner = serializers.SerializerMethodField("get_user")
    trigger = serializers.SerializerMethodField("get_user")
    runner = serializers.SerializerMethodField("get_runner")
    jobid = serializers.SerializerMethodField("get_jobid")

    payload = serializers.SerializerMethodField("get_payload")

    stdout = serializers.SerializerMethodField("get_stdout")
    jobdef = serializers.SerializerMethodField("get_jobdef")

    def get_payload(self, instance):
        payload = JobPayloadSerializer(instance.payload, many=False)
        return payload.data

    def get_stdout(self, instance):
        return instance.output.stdout

    def get_jobdef(self, instance):
        jobdef = instance.jobdef
        return {
            "name": jobdef.name,
            "uuid": jobdef.short_uuid,
        }

    def get_jobid(self, instance):
        # FIXME: this is to fix empty jobids from unran Celery jobs
        return instance.jobid

    def get_runner(self, instance):
        # FIXME: replace with actual values
        return {
            "name": "Python 3.8",
            "uuid": "1234-5678-9012-3456",
            "cpu_time": 140.568,
            "cpu_cores": 2,
            "memory_mib": 568,
            "job_status": 0,
        }

    def get_trigger(self, instance):
        # FIXME: return the real trigger source
        return "API"

    def get_version(self, instance):
        # FIXME: replace with actual version information
        return {
            "name": "latest",
            "uuid": "2222-3333-2222-2222",
        }

    def get_package(self, instance):
        # FIXME: replace with actual data after models refactor
        # package = instance.package
        package = instance.jobdef.project.packages.last()
        if package:
            return {
                "name": package.filename,
                "uuid": package.uuid,
            }
        return {
            "name": "latest",
            "uuid": None
        }

    def get_project(self, instance):
        project = instance.jobdef.project
        return {
            "name": project.name,
            "uuid": project.short_uuid,
        }

    def get_user(self, instance):
        if instance.owner:
            return {
                "name": instance.owner,
                "uuid": instance.owner.short_uuid,
            }
        return {
            "name": None,
            "uuid": None,
        }
    class Meta:
        model = JobRun
        fields = "__all__"


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
        jobpayload = instance.payload
        return {
            'uuid': instance.uuid,
            'payload': str(jobpayload),
            'status': instance.status,
            'runtime': instance.runtime,
            'memory': instance.memory,
            'return_payload': instance.output.return_payload,
            'stdout': instance.output.stdout,
            'created': instance.created,
            'finished': instance.output.created
        }
