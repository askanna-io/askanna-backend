from rest_framework import serializers

from job.models import JobDef


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDef
        fields = (
            'uuid', 
            'name', 
            'status',
        )
