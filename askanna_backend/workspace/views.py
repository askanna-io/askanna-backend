import django_filters
from core.permissions import RoleBasedPermission
from core.views import SerializerByActionMixin
from django.contrib.auth import get_user_model
from django.db.models import BooleanField, Exists, OuterRef, Q, Value
from django.http import Http404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, viewsets
from users.models import MSP_WORKSPACE, Membership
from workspace.models import Workspace
from workspace.serializers import WorkspaceCreateSerializer, WorkspaceSerializer

User = get_user_model()


class FilterByMembershipFilterSet(django_filters.FilterSet):
    membership = django_filters.CharFilter(field_name="membership", method="filter_membership")

    ordering = django_filters.OrderingFilter(
        fields=(
            ("created", "created"),
            ("is_member", "membership"),
            ("name", "name"),
        )
    )

    def filter_membership(self, queryset, name, value):
        # construct the full lookup expression.
        bool_value = value.lower() in ["1", "yes", "true"]
        lookup = "is_member"
        return queryset.filter(**{lookup: bool_value})

    class Meta:
        model = Workspace
        fields = ["membership"]


@extend_schema_view(
    list=extend_schema(description="List the workspaces you have access to"),
    retrieve=extend_schema(description="Get info from a specific workspace"),
    create=extend_schema(description="Create a new workspace"),
    update=extend_schema(description="Update a workspace"),
    partial_update=extend_schema(description="Update a workspace"),
    destroy=extend_schema(description="Remove a workspace"),
)
class WorkspaceViewSet(
    SerializerByActionMixin,
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Workspace.objects.filter(deleted__isnull=True)
    serializer_class = WorkspaceSerializer
    lookup_field = "suuid"
    permission_classes = [RoleBasedPermission]

    serializer_classes_by_action = {
        "post": WorkspaceCreateSerializer,
    }

    # Override default, remove OrderingFilter because we use the DjangoFilterBackend version
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterByMembershipFilterSet

    RBAC_BY_ACTION = {
        "list": [],  # anyone but list is limited to actual membership or public workspace
        "retrieve": ["workspace.info.view"],
        "create": ["askanna.workspace.create"],
        "destroy": ["workspace.remove"],
        "update": ["workspace.info.edit"],
        "partial_update": ["workspace.info.edit"],
    }

    def get_queryset(self):
        """
        Return only where the user is member of or has access to
        FIXME: get rid of the membership query here, store in redis in future
        """
        user = self.request.user
        if user.is_anonymous:
            return (
                super()
                .get_queryset()
                .filter(Q(visibility="PUBLIC"))
                .annotate(is_member=Value(False, BooleanField()))
                .order_by("name")
            )

        member_of_workspaces = user.memberships.filter(object_type=MSP_WORKSPACE, deleted__isnull=True).values_list(
            "object_uuid"
        )

        memberships = Membership.objects.filter(user=user, deleted__isnull=True, object_uuid=OuterRef("pk"))

        return (
            super()
            .get_queryset()
            .filter(Q(pk__in=member_of_workspaces) | Q(visibility="PUBLIC"))
            .annotate(is_member=Exists(memberships))
            .order_by("name")
        )

    def perform_destroy(self, instance):
        """
        We don't actually remove the model, we just mark it as deleted
        """
        instance.to_deleted()

    def get_object_role(self, request, *args, **kwargs):
        """
        To be executed before super().initial() in our custom initial
        - Setting current_object to Project/Workspace
        """
        object_role = None
        self.current_object = None
        self.current_object_type = "WS"
        if self.detail:
            try:
                self.current_object = Workspace.objects.get(suuid=kwargs.get("suuid"))
            except Workspace.DoesNotExist:
                raise Http404

            object_role, request.membership = Membership.get_workspace_role(request.user, self.current_object)
            return object_role
        return None

    def initial(self, request, *args, **kwargs):
        """
        Here we do a pre-initial call which sets the role of the user
        This was not possible in the standard Django middleware as DRF overwrites this with their own flow
        """
        # set the role and user_roles
        request.role = User.get_role(request)
        request.user_roles = [request.role]

        if getattr(self, "get_object_role"):
            object_role = self.get_object_role(request, *args, **kwargs)
            if object_role:
                request.user_roles.append(object_role)
                request.object_role = object_role

        super().initial(request, *args, **kwargs)
