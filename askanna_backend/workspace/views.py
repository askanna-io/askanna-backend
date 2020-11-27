import django_filters
from django.utils import timezone
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.schemas.openapi import AutoSchema
from rest_framework_extensions.mixins import NestedViewSetMixin

from users.models import MSP_WORKSPACE, Membership, Invitation
from users.permissions import (
    RequestHasAccessToWorkspacePermission,
    RequestIsValidInvite,
    RoleUpdateByAdminOnlyPermission,
)
from users.serializers import PersonSerializer
from workspace.models import Workspace
from workspace.serializers import WorkspaceSerializer


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
        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE, deleted__isnull=True).values_list(
            "object_uuid"
        )

        return self.queryset.filter(pk__in=member_of_workspaces)


class RoleFilterSet(django_filters.FilterSet):
    role = django_filters.CharFilter(field_name="role")

    class Meta:
        model = Membership
        fields = ["role"]


class PersonViewSet(
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Membership.objects.all()
    lookup_field = "short_uuid"
    serializer_class = PersonSerializer
    permission_classes = [
        RequestHasAccessToWorkspacePermission & RoleUpdateByAdminOnlyPermission,
    ]

    permission_classes_by_action = {
        "retrieve": [RequestIsValidInvite | RequestHasAccessToWorkspacePermission],
    }

    def get_permissions(self):
        try:
            # return permission_classes depending on `action`
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # action is not set return default permission_classes
            return [permission() for permission in self.permission_classes]

    def get_parents_query_dict(self):
        """This function retrieves the workspace uuid from the workspace short_uuid"""
        query_dict = super().get_parents_query_dict()
        short_uuid = query_dict.get("workspace__short_uuid")
        workspace = Workspace.objects.get(short_uuid=short_uuid)
        return {"object_uuid": workspace.uuid}

    def initial(self, request, *args, **kwargs):
        """This function sets the uuid from the query_dict and object_type as "WS" by default. """
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        request.data.update(parents)
        request.data["object_type"] = MSP_WORKSPACE

    def perform_create(self, serializer):
        """This function calls the send invite on the serializer and returns the instance"""
        instance = super().perform_create(serializer)
        serializer.send_invite()
        return instance

    def perform_update(self, serializer):
        """Extend update process to conditionally re-send invitation email."""
        super().perform_update(serializer)

        if serializer.get_status(serializer.instance) == "invited":
            serializer.send_invite()

    def perform_destroy(self, instance):
        """Delete invitations and soft-delete membersips."""
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            # This is no invitation, is a profile. Soft delete it.
            instance.deleted = timezone.now()
            instance.save()
        else:
            # This is an invitation, Hard delete it.
            instance.delete()
