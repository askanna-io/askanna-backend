from package.models import ChunkedPackagePart
from rest_framework import serializers


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    is_last = serializers.ReadOnlyField()
    deleted_at = serializers.ReadOnlyField()

    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"
