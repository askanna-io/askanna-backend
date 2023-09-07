from django.http import Http404
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser

from account.serializers.me import MeSerializer
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.role import RoleBasedPermission
from core.viewsets import AskAnnaGenericViewSet


class MeMixin(
    ObjectRoleMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    parser_classes = [MultiPartParser, JSONParser, FormParser]
    permission_classes = [RoleBasedPermission]

    def perform_destroy(self, instance):
        instance.to_deleted()


@extend_schema_view(
    retrieve=extend_schema(description="Get info of the authenticated account"),
    partial_update=extend_schema(description=("Update the info of the authenticated account.")),
    destroy=extend_schema(description="Remove the authenticated account from the platform"),
)
class MeViewSet(MeMixin):
    serializer_class = MeSerializer
    rbac_permissions_by_action = {
        "retrieve": ["askanna.me"],
        "partial_update": ["askanna.me.edit"],
        "destroy": ["askanna.me.remove"],
    }

    def get_object(self):
        """
        Return the current user as the object for this view. If the user is not active, raise HTTP status code 404.
        """
        user = self.request.user
        if user.is_anonymous or user.is_active:
            return user
        raise Http404
