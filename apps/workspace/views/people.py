import django_filters
from django.db.models import Case, Q, Value, When
from django.http import Http404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from account.models.membership import MSP_WORKSPACE, Invitation, Membership
from account.permissions import (
    RequestHasAccessToMembershipPermission,
    RequestIsValidInvite,
    RoleUpdateByAdminOnlyPermission,
)
from account.serializers.people import (
    AcceptInviteSerializer,
    InviteCheckEmail,
    InviteInfoSerializer,
    InviteSerializer,
    PeopleSerializer,
    ResendInviteSerializer,
    send_invite,
    validate_invite_status,
)
from core.filters import case_insensitive
from core.mixins import ObjectRoleMixin, PartialUpdateModelMixin
from core.permissions.askanna import RoleBasedPermission
from core.permissions.role_utils import get_user_workspace_role
from core.permissions.roles import WorkspaceAdmin, WorkspaceMember, WorkspaceViewer
from core.utils.config import get_setting
from core.viewsets import AskAnnaGenericViewSet
from workspace.models import Workspace


class PeopleFilterSet(django_filters.FilterSet):
    status = django_filters.MultipleChoiceFilter(
        choices=(("active", "active"), ("invited", "invited"), ("deleted", "deleted"), ("blocked", "blocked")),
        help_text="Filter on membership status.",
    )
    role_code = django_filters.MultipleChoiceFilter(
        field_name="role",
        choices=(
            ("wm", "workspace member"),
            ("wa", "workspace admin"),
            ("wv", "workspace viewer"),
        ),
        help_text="Filter on membership role.",
        method=case_insensitive,
    )
    email = django_filters.CharFilter(
        help_text="Filter people on email or multiple email addresses via a list separated by a comma.",
        method="filter_email",
    )

    def filter_email(self, queryset, name, value):
        values = list(map(lambda x: x.strip(), value.split(",")))
        q = Q()
        for value in values:
            q |= Q(invitation__email__iexact=value) | Q(user__email__iexact=value)
        return queryset.filter(q)


@extend_schema_view(
    list=extend_schema(description="List the people in a workspace"),
    retrieve=extend_schema(description="Get info from a person in a workspace"),
    partial_update=extend_schema(description="Update a person in a workspace"),
    destroy=extend_schema(description="Delete a person from a workspace"),
    invite=extend_schema(
        description="Invite a person to a workspace",
        responses={201: InviteSerializer},
    ),
    invite_check_email=extend_schema(
        description="Check if an email address is already a member of the workspace",
        parameters=[
            OpenApiParameter(
                "email", OpenApiTypes.EMAIL, OpenApiParameter.QUERY, many=True, description="Email address(es)"
            ),
        ],
        request=None,
    ),
    invite_info=extend_schema(
        description="Get invite info",
        parameters=[
            OpenApiParameter("token", OpenApiTypes.STR, OpenApiParameter.QUERY, description="Invite token"),
        ],
    ),
    invite_resend=extend_schema(
        description="If a membership is in the invited state, this endpoint will (re)send the invitation.",
        responses={204: None},
    ),
    invite_accept=extend_schema(
        description="If a membership is in the invited state, this endpoint will accept the invite and asign the "
        "membership to user who did the request. If the user is already a member of the workspace, the membership "
        "will not be assigned.",
        responses={204: None},
    ),
)
@extend_schema(
    parameters=[OpenApiParameter("parent_lookup_workspace__suuid", OpenApiTypes.STR, OpenApiParameter.PATH)],
)
class WorkspacePeopleViewSet(
    ObjectRoleMixin,
    NestedViewSetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    PartialUpdateModelMixin,
    mixins.DestroyModelMixin,
    AskAnnaGenericViewSet,
):
    queryset = (
        Membership.objects.active_members()
        .select_related(
            "avatar_file",
            "user__avatar_file",
            "invitation",
        )
        .annotate(
            status=Case(
                When(user__isnull=False, deleted_at__isnull=True, then=Value("active")),
                When(deleted_at__isnull=False, then=Value("deleted")),
                When(invitation__isnull=False, then=Value("invited")),
                default=Value("blocked"),
            ),
            member_name=Case(
                When(use_global_profile=True, then="user__name"),
                When(use_global_profile=False, then="name"),
            ),
            member_job_title=Case(
                When(use_global_profile=True, then="user__job_title"),
                When(use_global_profile=False, then="job_title"),
            ),
        )
    )
    search_fields = ["suuid", "member_name", "user__email", "invitation__email"]
    ordering_fields = [
        "created_at",
        "modified_at",
        "name",
        "job_title",
        "status",
        "role",
    ]
    ordering_fields_aliases = {
        "name": "member_name",
        "job_title": "member_job_title",
    }
    filterset_class = PeopleFilterSet

    parser_classes = [MultiPartParser, JSONParser]

    serializer_class = PeopleSerializer

    permission_classes = [
        RoleBasedPermission,
        RoleUpdateByAdminOnlyPermission,
        RequestHasAccessToMembershipPermission,
    ]
    rbac_permissions_by_action = {
        "list": ["workspace.people.list"],
        "retrieve": ["workspace.people.list"],
        "destroy": ["workspace.people.remove", "workspace.people.invite.remove"],
        "update": ["workspace.people.edit"],
        "partial_update": ["workspace.people.edit", "workspace.me.edit"],
        "invite": ["workspace.people.invite.create"],
        "invite_check_email": ["workspace.people.invite.create"],
        "invite_info": ["workspace.people.invite.info"],
        "invite_accept": ["askanna.member"],
        "invite_resend": ["workspace.people.invite.resend"],
    }

    def get_parents_query_dict(self):
        """This function retrieves the workspace uuid from the workspace suuid"""
        query_dict = super().get_parents_query_dict()

        self.workspace_suuid = query_dict.get("workspace__suuid")
        try:
            self.workspace = Workspace.objects.get(suuid=self.workspace_suuid)
        except Workspace.DoesNotExist as exc:
            raise Http404 from exc

        return {
            "object_uuid": self.workspace.uuid,
            "object_type": MSP_WORKSPACE,
        }

    def get_object_workspace(self):
        return self.workspace

    def get_parrent_roles(self, request, *args, **kwargs):
        return [self.get_workspace_role(request.user)]

    def initial(self, request, *args, **kwargs):
        """
        This function sets the request user roles, object uuid and object type from the query_dict.

        First, it calls the get_parents_query_dict function to retrieve the workspace object that is than used in
        ObjectRoleMixin.initial
        """
        self.request_data = request.data.copy()
        self.request_data.update(self.get_parents_query_dict())

        workspace_role = get_user_workspace_role(request.user, self.workspace)
        self.request_user_workspace_role = workspace_role
        self.request_user_is_workspace_member = workspace_role in [WorkspaceMember, WorkspaceAdmin, WorkspaceViewer]
        self.request_user_is_workspace_admin = workspace_role in [WorkspaceAdmin]

        super().initial(request, *args, **kwargs)

    def perform_destroy(self, instance):
        """Delete invitations and soft-delete memberships."""
        try:
            _ = instance.invitation
        except Invitation.DoesNotExist:
            # This is an active membership. Soft-delete it.
            instance.to_deleted(removed_by=self.request.user)
        else:
            # This is an invitation. Hard-delete it.
            instance.delete()

    @action(
        detail=False,
        methods=["post"],
        serializer_class=InviteSerializer,
    )
    def invite(self, request, **kwargs):
        serializer = self.get_serializer(data=self.request_data)
        serializer.is_valid(raise_exception=True)
        serializer.create(serializer.validated_data)
        return Response(serializer.data, status=201)

    @action(
        detail=False,
        methods=["get"],
        serializer_class=InviteCheckEmail,
        url_path="invite/check-email",
    )
    def invite_check_email(self, request, **kwargs):
        serializer = self.get_serializer(data=self.request_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=200)

    @action(
        detail=True,
        methods=["get"],
        serializer_class=InviteInfoSerializer,
        permission_classes=[RequestIsValidInvite | (RoleBasedPermission & RequestHasAccessToMembershipPermission)],
        url_path="invite/info",
    )
    def invite_info(self, request, **kwargs):
        instance = self.get_object()
        try:
            serializer = self.get_serializer(instance.invitation)
        except Invitation.DoesNotExist as exc:
            raise Http404 from exc

        return Response(serializer.data, status=200)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=ResendInviteSerializer,
        url_path="invite/resend",
    )
    def invite_resend(self, request, **kwargs):
        instance = self.get_object()
        validate_invite_status(instance)

        resend_serializer = self.get_serializer(data=self.request_data)
        resend_serializer.is_valid(raise_exception=True)
        front_end_url = resend_serializer.validated_data.get("front_end_url", get_setting("ASKANNA_UI_URL"))

        send_invite(instance, front_end_url=front_end_url)

        return Response(None, status=204)

    @action(
        detail=True,
        methods=["post"],
        serializer_class=AcceptInviteSerializer,
        url_path="invite/accept",
    )
    def invite_accept(self, request, **kwargs):
        instance = self.get_object()

        serializer = self.get_serializer(instance, data=self.request_data)
        serializer.is_valid(raise_exception=True)
        serializer.set_membership_to_accepted()

        return Response(None, status=204)
