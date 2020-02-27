from rest_framework import serializers

from package.models import Package, ChunkedPackagePart


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = (
            'uuid',
            'filename',
            'storage_location',
            'project_id',
            'size',
            'created_by',
            'created_at'
        )


class ChunkedPackagePartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChunkedPackagePart
        fields = (
            'uuid',
            'filename',
            'size',
            'file_no',
            'is_last',
            'package',
            'created_at'
        )