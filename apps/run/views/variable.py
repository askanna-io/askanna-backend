from django.core.cache import cache
from django.db.models import Q
from django_filters import CharFilter, FilterSet
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status
from rest_framework.response import Response

from core.filters import filter_array
from core.mixins import SerializerByActionMixin
from core.permissions import AskAnnaPermissionByAction
from core.views import get_object_or_404
from core.viewsets import AskAnnaGenericViewSet
from run.models import Run, RunVariable
from run.serializers.variable import RunVariableSerializer, RunVariableUpdateSerializer


class RunVariableFilterSet(FilterSet):
    variable_name = CharFilter(field_name="variable__name")
    variable_value = CharFilter(field_name="variable__value")
    variable_type = CharFilter(field_name="variable__type")

    label_name = CharFilter(field_name="label__*__name", method=filter_array)
    label_value = CharFilter(field_name="label__*__value", method=filter_array)
    label_type = CharFilter(field_name="label__*__type", method=filter_array)


class RunVariableView(
    SerializerByActionMixin,
    mixins.ListModelMixin,
    AskAnnaGenericViewSet,
):
    """List run variables"""

    queryset = RunVariable.objects.active(add_select_related=True)
    max_page_size = 10000  # For variable listings we want to allow "a lot" of data in a single request
    search_fields = ["variable__name"]
    ordering_fields = [
        "created_at",
        "variable.name",
        "variable.value",
        "variable.type",
    ]
    filterset_class = RunVariableFilterSet
    permission_classes = [AskAnnaPermissionByAction]

    serializer_class_by_action = {
        "variable_list": RunVariableSerializer,
        "variable_update": RunVariableUpdateSerializer,
    }

    def get_queryset(self):
        """
        For listings return only values from runs in projects where the request user has access to
        """
        return self.queryset.filter(
            Q(run__jobdef__project__workspace__in=self.member_of_workspaces)
            | (Q(run__jobdef__project__workspace__visibility="PUBLIC") & Q(run__jobdef__project__visibility="PUBLIC")),
            run__suuid=self.kwargs["suuid"],
        )

    def get_object(self) -> Run:
        queryset = Run.objects.active().select_related("jobdef__project__workspace")
        obj = get_object_or_404(queryset, suuid=self.kwargs["suuid"])
        self.check_object_permissions(self.request, obj)
        return obj

    @extend_schema(
        summary="List run variables",
        filters=True,
    )
    def variable_list(self, request, *args, **kwargs):
        """List run variables for a specific run"""
        # Although the purpose is to GET a list of run variables, the request is actual a detail request on a Run
        # object. That's why we first run get_object to check permissions for the requested Run object.
        self.get_object()

        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Update run variables",
        responses={status.HTTP_204_NO_CONTENT: None},
    )
    def variable_update(self, request, *args, **kwargs):
        """Update run variables for a specific run"""
        instance = self.get_object()

        lock_key = f"run.RunVariable:update:{instance.suuid}"
        if cache.get(lock_key):
            return Response({"detail": "These run's variables are currently being updated"}, status.HTTP_409_CONFLICT)

        cache.set(lock_key, True, timeout=60)
        try:
            serializer = self.get_serializer(instance, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.update()
        finally:
            cache.delete(lock_key)

        return Response(None, status.HTTP_204_NO_CONTENT)
