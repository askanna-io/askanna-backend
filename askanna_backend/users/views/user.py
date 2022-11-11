from core.views import PermissionByActionMixin, SerializerByActionMixin
from django.contrib.auth import get_user_model
from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin
from users.models import MSP_WORKSPACE, Invitation, Membership
from users.permissions import (
    IsNotAlreadyMember,
    IsOwnerOfUser,
    RequestHasAccessToMembershipPermission,
    RequestIsValidInvite,
    RoleUpdateByAdminOnlyPermission,
)
from users.serializers import (
    PersonSerializer,
    ProfileImageSerializer,
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
)
from workspace.models import Workspace

User = get_user_model()


class UserView(
    SerializerByActionMixin,
    PermissionByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "suuid"
    serializer_class = UserSerializer

    permission_classes_by_action = {
        "list": [IsAdminUser],
        "create": [IsNotAlreadyMember],
        "update": [IsOwnerOfUser],
        "partial_update": [IsOwnerOfUser],
    }

    serializer_classes_by_action = {
        "post": UserCreateSerializer,
        "put": UserUpdateSerializer,
        "patch": UserUpdateSerializer,
    }


class PersonViewSet(
    PermissionByActionMixin,
    NestedViewSetMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Membership.members.members()
    lookup_field = "suuid"
    serializer_class = PersonSerializer
    permission_classes = [
        RoleUpdateByAdminOnlyPermission,
        RequestHasAccessToMembershipPermission,
    ]

    permission_classes_by_action = {
        "retrieve": [RequestIsValidInvite | RequestHasAccessToMembershipPermission],
    }

    def get_parents_query_dict(self):
        """This function retrieves the workspace uuid from the workspace suuid"""
        query_dict = super().get_parents_query_dict()
        suuid = query_dict.get("workspace__suuid")
        workspace = Workspace.objects.get(suuid=suuid)
        return {"object_uuid": workspace.uuid}

    def initial(self, request, *args, **kwargs):
        """This function sets the uuid from the query_dict and object_type as "WS" by default."""
        super().initial(request, *args, **kwargs)
        parents = self.get_parents_query_dict()
        request.data.update(parents)
        request.data["object_type"] = MSP_WORKSPACE

    def perform_destroy(self, instance):
        """Delete invitations and soft-delete membersips."""
        try:
            instance.invitation
        except Invitation.DoesNotExist:
            # This is no invitation, is a profile. Soft delete it.

            # setting the membership to deleted will automaticly read `use_global_profile`
            # to copy over some info from User object
            instance.to_deleted()
        else:
            # This is an invitation, Hard delete it.
            instance.delete()

    @action(
        detail=True,
        methods=["patch", "delete"],
        name="Set user profileimage",
    )
    def avatar(self, request, **kwargs):
        instance = self.get_object()

        if request.method.lower() == "delete":
            # delete avatar
            instance.delete_avatar()
            return Response("", status=204)

        serializer = ProfileImageSerializer(
            instance=instance,
            data=request.data,
        )
        # will raise exeptions when needed
        serializer.is_valid(raise_exception=True)

        # save the image to the userprofile
        serializer.save()
        return Response({"valid": True})
