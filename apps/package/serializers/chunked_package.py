from rest_framework import serializers

from package.models import ChunkedPackagePart


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    is_last = serializers.ReadOnlyField()
    deleted_at = serializers.ReadOnlyField()

    class Meta:
        model = ChunkedPackagePart
        fields = "__all__"
