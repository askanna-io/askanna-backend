from rest_framework import serializers

from project.models import Project


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
<<<<<<< HEAD
        fields = '__all__'
=======
        fields = '__all__'
>>>>>>> origin/master
