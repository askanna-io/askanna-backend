from rest_framework import serializers

from project_template.models import ProjectTemplate


class ProjectTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectTemplate
        fields = "__all__"
