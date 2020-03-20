from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated



from drf_yasg import openapi

from job.models import JobDef, Job, get_job_pk
from job.serializers import JobSerializer, JobRunTestSerializer, StartJobSerializer


class StartJobView(viewsets.GenericViewSet):
    queryset = JobDef.objects.all()
    lookup_field = 'uuid'
    serializer_class = StartJobSerializer
    permission_classes = [IsAuthenticated]

    def do_ingest(self, request, uuid, **kwargs):
        """
        We accept any data that is sent in request.data
        The provided `uuid` is really existing, as this is checked by the .get_object
        We specificed the `lookup_field` to search for uuid.
        """
        jobdef = self.get_object()
        print(kwargs)
        print(request.data)
        print(request.POST)
        print(request.GET)
        print(request.FILES)
        return Response({"status": f"We are starting the job for {uuid}"})

class JobActionView(viewsets.ModelViewSet):
    queryset = JobDef.objects.all()
    serializer_class = JobSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], name='Start job')
    def start(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        job.start()
        return Response({'status': 'started'})

    @action(detail=True, methods=['post'], name='Stop job')
    def stop(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        job.stop()
        return Response({'status': 'stopped'})

    @action(detail=True, methods=['post'], name='Pause job')
    def pause(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        job.pause()
        return Response({'status': 'paused'})

    @action(detail=True, methods=['post'], name='Reset job')
    def reset(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        job.stop()
        return Response({'status': 'reset'})

    @action(detail=True, methods=['post'], name='Job info')
    def info(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        #return Response({'status': 'info'})
        return Response({'status': job.info()})

    @action(detail=True, methods=['post'], name='Kill job')
    def kill(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        job.kill()
        return Response({'status': 'killed'})

    @action(detail=True, methods=['post'], name='Result job')
    def result(self, request, pk=None):
        #job = Job(pk=pk)
        #job = get_job(uuid)
        job = get_job_pk(pk)
        #job.result()
        return Response({'result': job.result()})

    @action(detail=True, methods=['post'], name='Job Runs')
    def runs(self, request, pk=None):
        job = get_job_pk(pk)
        runs = JobRunTestSerializer(job.runs(), many=True)
        return Response(runs.data)

    @action(detail=True, methods=['post'], name='Job Status')
    def status(self, request, pk=None):
        job = get_job_pk(pk)
        return Response({'status': job.status()})
