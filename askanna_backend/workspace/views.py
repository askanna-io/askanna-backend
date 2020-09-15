from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import Membership, UserProfile
from users.serializers import MembershipSerializer, UpdateUserRoleSerializer, UserProfileSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.permissions import IsMemberOrAdminUser
from resumable.files import ResumableFile
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from core.mixins import HybridUUIDMixin
from users.models import Membership, MSP_WORKSPACE
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer

from rest_framework.schemas.openapi import AutoSchema
from rest_framework import status

class MySchema(AutoSchema):
    def get_tags(self, path, method):
        return ["workspace"]


class WorkspaceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceSerializer
    lookup_field = "short_uuid"
    schema = MySchema()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Return only where the user is member of or has access to
        FIXME: get rid of the query here, store in redis in future
        """
        user = self.request.user
        member_of_workspaces = user.memberships.filter(
            object_type=MSP_WORKSPACE
        ).values_list("object_uuid")

        return self.queryset.filter(pk__in=member_of_workspaces)


class RoleFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name='role')

    class Meta:
        model = Membership
        fields = ['role']


class MembershipView(
    NestedViewSetMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer()
    lookup_field = 'short_uuid'
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    ordering = ['user__name']
    ordering_fields = ['user__name']
    filterset_class = RoleFilterSet
    permission_classes = [IsMemberOrAdminUser]

    def get_parents_query_dict(self):
        query_dict = super().get_parents_query_dict()
        key = 'workspace__short_uuid'
        val = query_dict.get(key)
        short_uuid = val
        workspace = Workspace.objects.get(short_uuid=short_uuid)
        return {'object_uuid': workspace.uuid}


class UserProfileView(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DeleteMixin,
    viewsets.GenericViewSet,
):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer()
    lookup_field = 'short_uuid'
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    ordering = ['user__name']
    ordering_fields = ['user__name']
    filterset_class = RoleFilterSet
    permission_classes = [IsMemberOrAdminUser]

    def get_parents_query_dict(self):
        query_dict = super().get_parents_query_dict()
        key = 'workspace__short_uuid'
        val = query_dict.get(key)
        short_uuid = val
        workspace = Workspace.objects.get(short_uuid=short_uuid)
        return {'object_uuid': workspace.uuid}
