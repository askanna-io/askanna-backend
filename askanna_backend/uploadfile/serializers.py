import json

from rest_framework import serializers

from .models import DummyFile


class DummyFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DummyFile
        fields = ('uploadedfile',)
