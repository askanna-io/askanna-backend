from package.models import Package
from rest_framework import serializers


class PackageRelationSerializer(serializers.ModelSerializer):
    relation = serializers.SerializerMethodField()
    suuid = serializers.ReadOnlyField()
    name = serializers.ReadOnlyField(source="original_filename")

    def get_relation(self, instance) -> str:
        return self.Meta.model.__name__.lower()

    class Meta:
        model = Package
        fields = [
            "relation",
            "suuid",
            "name",
        ]
