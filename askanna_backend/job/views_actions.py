import json

from drf_yasg import openapi

from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework_extensions.mixins import NestedViewSetMixin

from core.mixins import HybridUUIDMixin
from job.models import JobDef, Job, get_job_pk, JobPayload, get_job, JobRun
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
        print(request.query_params) # same as request.GET from django
        print(request.FILES)

        # validate whether request.data is really a json structure

        # store incoming data as payload (in file format)
        with open('/tmp/random.json', 'w') as f:
            f.write(json.dumps(request.data))

        # create new JobPayload
        job_pl = JobPayload.object.create(
            jobdef=jobdef,
            payload=request.data,
            owner=1 # FIXME: do a lookup on request.user
            )

        # create new Jobrun
        jobrun = JobRun.objects.create(
            jobdef=jobdef,
            payload=job_pl.uuid)

        # return the JobRun id
        return Response({
            "status": "started", 
            "job_uuid": jobrun.uuid,
            "status_uri": "https://api.askanna.io/api/v1/job/"
        })

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

class ProjectJobViewSet(HybridUUIDMixin, NestedViewSetMixin, viewsets.ReadOnlyModelViewSet):

    queryset = JobDef.objects.all()
    serializer_class = JobSerializer

    # overwrite the default view and serializer for detail page
    # we want to use an other serializer for this.
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer_kwargs = {}
        serializer_kwargs['context'] = self.get_serializer_context()
        serializer = JobSerializer(instance, **serializer_kwargs)
        return Response(serializer.data)
