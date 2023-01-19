from core.mixins import (
    PartialUpdateModelMixin,
    PermissionByActionMixin,
    SerializerByActionMixin,
)
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from users.models import User
from users.permissions import IsNotMember, IsOwnerOfUser
from users.serializers.account import AccountSerializer, AccountUpdateSerializer


@extend_schema_view(
    list=extend_schema(description="List the accounts you have access to"),
    create=extend_schema(description="Create a new account"),
    retrieve=extend_schema(description="Get info from an account"),
    partial_update=extend_schema(description="Update an account"),
)
class AccountViewSet(
    PermissionByActionMixin,
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = "suuid"
    search_fields = ["suuid", "name", "email"]

    serializer_class = AccountSerializer
    serializer_class_by_action = {
        "partial_update": AccountUpdateSerializer,
    }

    permission_classes_by_action = {
        "list": [IsAdminUser],
        "retrieve": [IsOwnerOfUser | IsAdminUser],
        "create": [IsNotMember | IsAdminUser],
        "partial_update": [IsOwnerOfUser],
    }
