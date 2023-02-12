import pytest
from account.models import (
    MSP_WORKSPACE,
    WS_ADMIN,
    WS_MEMBER,
    Invitation,
    User,
    UserProfile,
)
from django.core import mail
from django.db.models import signals
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from ..listeners import install_demo_project_in_workspace
from ..models import Workspace

pytestmark = pytest.mark.django_db


class TestInviteAPI(APITestCase):
    @classmethod
    def setup_class(cls):
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)

    def setUp(self):
        self.users = {
            "admin": User.objects.create(username="admin", email="admin@example.com"),
            "member_a": User.objects.create(username="member_a", email="member_a@example.com"),
            "user_a": User.objects.create(username="user_a", email="user_a@example.com"),
        }
        self.workspace = Workspace.objects.create(name="test workspace")
        self.workspace2 = Workspace.objects.create(name="test workspace2")
        self.invitation = Invitation.objects.create(
            object_uuid=self.workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="invited@example.com",
            use_global_profile=False,
        )

        # make the admin user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin"],
            role=WS_ADMIN,
            use_global_profile=False,
        )
        # make the member_a user member of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
            use_global_profile=False,
        )
        # make the member_a user member of the workspace2
        self.member_profile2 = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace2.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
            name="name2",
            use_global_profile=False,
        )

    def test_retrieve_invite_as_anonymous_with_token(self):
        """Anonymous users need to send the token to retrieve an invite."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        response = self.client.get(url, {"token": self.invitation.generate_token()})

        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.invitation.suuid}.items() <= dict(response.data).items()  # type: ignore

    def test_retrieve_invite_as_anonymous_without_token(self):
        """With no token, invites are not available to anonymous users."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        response = self.client.get(
            url,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_invite_info_askanna_member_with_token(self):
        """Authenticated users can retrieve an invite with a valid token."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(url, {"token": self.invitation.generate_token()})

        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.invitation.suuid}.items() <= dict(response.data).items()  # type: ignore

    def test_retrieve_invite_info_askanna_member_without_token(self):
        """Authenticated need a token to retrieve an invite."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_retrieve_invite_info_as_member(self):
        """A member can see existing invitations from a workspace."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.invitation.suuid}.items() <= dict(response.data).items()  # type: ignore

    def test_retrieve_invite_info_as_admin(self):
        """An admin can see existing invitations from a workspace."""
        url = reverse(
            "workspace-people-invite-info",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert {"suuid": self.invitation.suuid}.items() <= dict(response.data).items()  # type: ignore

    def test_create_invite(self):
        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": "anna_test@askanna.dev"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert {"email": "anna_test@askanna.dev"}.items() <= dict(response.data).items()  # type: ignore

    def test_create_double_invite_not_possible(self):
        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": "invited@example.com"},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_cannot_invite_active_member(self):
        """An invitation to an email of an existing member can not be created."""
        profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
        )

        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": profile.user.email},
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_can_invite_removed_member(self):
        """An invitation to an email of a soft-deleted profile can be created."""
        profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
            deleted=timezone.now(),
        )

        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": profile.user.email},
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_admin_can_revoke_invite(self):
        """Admins of a workspace can revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Invitation.objects.filter(uuid=self.invitation.uuid).exists()

    def test_member_can_revoke_invite(self):
        """Members of a workspace can revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Invitation.objects.filter(uuid=self.invitation.uuid).exists()

    def test_non_workspace_member_cannot_revoke_invite(self):
        """Non members of a workspace can not revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Invitation.objects.filter(uuid=self.invitation.uuid).exists()

    def test_admin_cannot_revoke_invitation_from_other_workspace(self):
        """Revoking an invitation is limited to workspaces a user is member of."""
        extra_workspace = Workspace.objects.create(name="extra test workspace")
        extra_invitation = Invitation.objects.create(
            object_uuid=extra_workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="extra@example.com",
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": extra_workspace.suuid,
                "suuid": extra_invitation.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Invitation.objects.filter(uuid=self.invitation.uuid).exists()

    @override_settings(ASKANNA_INVITATION_VALID_HOURS=0)
    def test_invite_token_expired(self):
        """An expired token is not good for accepting an invitation."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": self.invitation.generate_token(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data  # type: ignore
        assert response.data["token"][0] == "Token expired"  # type: ignore

    def test_create_invite_as_non_member(self):
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": "anna_test@askanna.dev"},
            format="json",
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_invite_for_admin_as_workspace_admin(self):
        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "email": "anna_test@askanna.dev",
                "role_code": "WA",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED

    def test_create_invite_for_admin_as_workspace_member(self):
        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "email": "anna_test@askanna.dev",
                "role_code": "WA",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_accept_invite(self):
        """After accepting an invite, a new Profile exists."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": self.invitation.generate_token(),
            },
            format="json",
        )
        profile = UserProfile.objects.get(pk=self.invitation.pk)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Invitation.objects.filter(pk=self.invitation.pk).exists()
        assert profile.user == self.users["user_a"]
        assert profile.object_uuid == self.workspace.uuid

    def test_existing_workspace_member_cannot_accept_invite(self):
        """An existing member can not accept an invite to the same workspace."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": self.invitation.generate_token(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"][0] == "Account is already member of this workspace"  # type: ignore

    def test_accept_invite_with_deleted_profile(self):
        """An invite can be accepted by a user with a soft-deleted profile."""
        UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
            deleted=timezone.now(),
        )

        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(url, {"token": self.invitation.generate_token()}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_accept_invite_requires_authentication(self):
        """An anonymous user can not accept an invite."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        response = self.client.post(url, {}, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_accept_invite_token_validated(self):
        """A token error is returned on invalid token."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": "fake_token",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data  # type: ignore
        assert response.data["token"][0] == "Token is not valid"  # type: ignore

    def test_accept_invite_token_is_required(self):
        """A missing token error is returned when token is missing."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(url)

        assert response.status_code, status.HTTP_400_BAD_REQUEST

    def test_accept_accepted_invite(self):
        """Accepting an already accepted invitation fails."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.member_profile.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": self.invitation.generate_token(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data  # type: ignore
        assert response.data["token"][0] == "Token is not valid"  # type: ignore

    def test_accept_invite_with_token_for_wrong_invitation(self):
        """Use token for wrong invitation fails."""
        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        to_fail_invitation = Invitation.objects.create(
            object_uuid=self.workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="will_fail@example.com",
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": to_fail_invitation.generate_token(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data  # type: ignore
        assert response.data["token"][0] == "Token is not valid"  # type: ignore

    def test_accept_invite_for_wrong_workspace_fails(self):
        """The invitation must be for the correct workspace."""
        to_fail_workspace = Workspace.objects.create(name="will fail workspace")

        url = reverse(
            "workspace-people-invite-accept",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": to_fail_workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {
                "token": self.invitation.generate_token(),
            },
            format="json",
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_list_limited_to_current_workspace(self):
        """Listing of people is correctly filtered to requested workspace."""
        new_workspace = Workspace.objects.create(name="test workspace")
        filtered_invitation = Invitation.objects.create(
            object_uuid=new_workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="invited@example.com",
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

        suuids = [p["suuid"] for p in response.data["results"]]  # type: ignore

        assert len(suuids) == 4
        assert str(filtered_invitation.suuid) not in suuids
        assert str(self.invitation.suuid) in suuids
        assert str(self.member_profile.suuid) in suuids

    def test_invitation_data_is_not_writable(self):
        """Data from an invitation is read only once it has been created."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            url,
            {"email": "invalid", "object_uuid": "invalid", "object_type": "invalid"},
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["workspace"]["suuid"] == str(self.workspace.suuid)  # type: ignore

    def test_non_member_can_not_modify_invitation(self):
        """An non member can not modify an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(url, {"email": "new@example.com"}, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_creating_invite_sends_invitation_email(self):
        """After creating an invitation, an invitation email is sent."""
        url = reverse(
            "workspace-people-invite",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(
            url,
            {"email": "anna_test@askanna.dev"},
            format="json",
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert mail.outbox[0].subject == f"You’re invited to join {self.workspace.name} on AskAnna"

    def test_resend_invitation_email(self):
        """Resend an invitation email"""
        url = reverse(
            "workspace-people-invite-resend",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.invitation.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.post(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert mail.outbox[0].subject == f"You’re invited to join {self.workspace.name} on AskAnna"

    def test_modify_membership_name(self):
        """Change the name in the membership"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.member_profile.suuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            url,
            {
                "name": "new-name",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "name" in response.data  # type: ignore
        assert response.data["name"] == "new-name"  # type: ignore

    def test_modify_membership_name_should_not_affect_other_workspace_profiles(self):
        """Change the name in the membership"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace.suuid,
                "suuid": self.member_profile.suuid,
            },
        )

        url2 = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__suuid": self.workspace2.suuid,
                "suuid": self.member_profile2.suuid,
            },
        )
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)  # type: ignore

        response = self.client.patch(
            url,
            {
                "name": "new-name",
            },
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "name" in response.data  # type: ignore
        assert response.data["name"] == "new-name"  # type: ignore

        response = self.client.patch(
            url2,
            format="json",
        )

        assert response.status_code == status.HTTP_200_OK
        assert "name" in response.data  # type: ignore
        assert response.data["name"] == "name2"  # type: ignore
