from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser

from job.models import JobDef, Job
from job.serializers import JobSerializer


from drf_yasg import openapi

class JobActionView(viewsets.ModelViewSet):
    queryset = JobDef.objects.all()
    serializer_class = JobSerializer

    @action(detail=True, methods=['post'], name='Start job')
    def start(self, request, pk=None):
        job = Job(pk=pk)
        job.start()
        return Response({'status': 'started'})

    @action(detail=True, methods=['post'], name='Stop job')
    def stop(self, request, pk=None):
        job = Job(pk=pk)
        job.stop()
        return Response({'status': 'stopped'})

    @action(detail=True, methods=['post'], name='Pause job')
    def pause(self, request, pk=None):
        job = Job(pk=pk)
        job.pause()
        return Response({'status': 'paused'})

    @action(detail=True, methods=['post'], name='Reset job')
    def reset(self, request, pk=None):
        job = Job(pk=pk)
        job.stop()
        return Response({'status': 'reset'})

    @action(detail=True, methods=['get'], name='Job info')
    def info(self, request, pk=None):
        job = Job(pk=pk)
        job.info()
        return Response({'status': 'info'})

    @action(detail=True, methods=['post'], name='Kill job')
    def kill(self, request, pk=None):
        job = Job(pk=pk)
        job.kill()
        return Response({'status': 'killed'})
