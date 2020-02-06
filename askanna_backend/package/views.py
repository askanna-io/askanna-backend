from django.shortcuts import render

from package.models import Package, ChunkedPackagePart
from package.serializers import PackageSerializer, ChunkedPackagePartSerializer
from rest_framework import viewsets

class PacakgeViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = Package.objects.all()
    serializer_class = PackageSerializer


class ChunkedPackagePartViewSet(viewsets.ModelViewSet):
    """
    A simple ViewSet for viewing and editing accounts.
    """
    queryset = ChunkedPackagePart.objects.all()
    serializer_class = ChunkedPackagePartSerializer
