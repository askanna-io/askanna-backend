from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from rest_framework import mixins, viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import Membership, UserProfile, Invitation
from users.serializers import UserProfileSerializer, PersonSerializer
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import filters
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.permissions import IsMemberOrAdminUser, IsAdminUser, RoleUpdateByAdminOnlyPermission, RequestHasAccessToWorkspacePermission
from resumable.files import ResumableFile
import django_filters
from django_filters.rest_framework import DjangoFilterBackend
from core.mixins import HybridUUIDMixin
from users.models import Membership, MSP_WORKSPACE
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

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


class UserProfileView(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    lookup_field = 'short_uuid'
    filter_backends = (filters.OrderingFilter, DjangoFilterBackend)
    ordering = ['user__name']
    ordering_fields = ['user__name']
    filterset_class = RoleFilterSet
    permission_classes = [IsMemberOrAdminUser]

    def get_parents_query_dict(self):
        query_dict = super().get_parents_query_dict()
        short_uuid = query_dict.get('workspace__short_uuid')
        workspace = Workspace.objects.get(short_uuid=short_uuid)
        return {'object_uuid': workspace.uuid}


class PersonViewSet(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Membership.objects.all()
    lookup_field = "short_uuid"
    serializer_class = PersonSerializer
    permission_classes = [RoleUpdateByAdminOnlyPermission, RequestHasAccessToWorkspacePermission]

    def get_parents_query_dict(self):
        """This function retrieves the workspace uuid from the workspace short_uuid"""
        query_dict = super().get_parents_query_dict()
        short_uuid = query_dict.get('workspace__short_uuid')
        workspace = Workspace.objects.get(short_uuid=short_uuid)
        return {'object_uuid': workspace.uuid}

    def send_invite(self, serializer):
        """ This function generates the token when the invitation is send.
        A mail is sent to the email that is given as input when creating the invitation"""
        email = serializer.data['email']
        token = serializer.generate_token()
        query_dict = super().get_parents_query_dict()
        short_uuid = query_dict.get('workspace__short_uuid')
        workspace = Workspace.objects.get(short_uuid=short_uuid)

        data = {
            'token': token,
            'workspace_name': workspace,
            'workspace_short_uuid': short_uuid,
            'web_ui_url': "https://askanna.eu",
            'people_short_uuid': serializer.data['short_uuid'],
        }

        subject = f'You’re invited to join {workspace} on AskAnna'
        from_email =  settings.DEFAULT_FROM_EMAIL

        text_version = render_to_string('emails/invitation_email.txt', data)
        html_version = render_to_string('emails/invitation_email.html', data)

        msg = EmailMultiAlternatives(subject, text_version, from_email, [email])
        msg.attach_alternative(html_version, "text/html")
        msg.send()

    def initial(self, request, *args, **kwargs):
        """This function sets the uuid from the query_dict and object_type as "WS" by default. """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        request.data.update(parents)
        request.data["object_type"] = "WS"

    def perform_create(self, serializer):
        """This function calls the send invite on the serializer and returns the instance"""
        instance = super().perform_create(serializer)
        self.send_invite(serializer)
        return instance