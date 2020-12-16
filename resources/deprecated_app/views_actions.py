from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser

from flow.models import FlowDef
from flow.flowinterface import get_flow_pk
from flow.serializers import FlowSerializer


class FlowActionView(viewsets.ModelViewSet):
    queryset = FlowDef.objects.all()
    serializer_class = FlowSerializer

    @action(detail=True, methods=['post'], name='Start flow')
    def start(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.start()
        return Response({'status': 'started'})

    @action(detail=True, methods=['post'], name='Stop job')
    def stop(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.stop()
        return Response({'status': 'stopped'})

    @action(detail=True, methods=['post'], name='Pause job')
    def pause(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.pause()
        return Response({'status': 'paused'})

    @action(detail=True, methods=['post'], name='Reset job')
    def reset(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.stop()
        return Response({'status': 'reset'})

    @action(detail=True, methods=['get'], name='Job info')
    def info(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.info()
        return Response({'status': 'info'})

    @action(detail=True, methods=['post'], name='Kill job')
    def kill(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.kill()
        return Response({'status': 'killed'})

    @action(detail=True, methods=['post'], name='Result job')
    def result(self, request, pk=None):
        # flow = Flow(pk=pk)
        flow = get_flow_pk(pk)
        flow.result()
        return Response({'status': flow.result()})
