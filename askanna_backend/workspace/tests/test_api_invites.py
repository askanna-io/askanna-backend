"""Define tests for API of invitation workflow."""
import pytest
from django.core import mail
from django.db.models import signals
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import (
    MSP_WORKSPACE,
    WS_ADMIN,
    WS_MEMBER,
    Invitation,
    User,
    UserProfile,
)
from users.serializers import PersonSerializer

from ..models import Workspace
from ..listeners import install_demo_project_in_workspace

pytestmark = pytest.mark.django_db

class TestInviteAPI(APITestCase):
    @classmethod
    def setup_class(cls):
        signals.post_save.disconnect(install_demo_project_in_workspace, sender=Workspace)

    def setUp(self):
        self.users = {
            "admin": User.objects.create(username="admin", email="admin@example.com"),
            "member_a": User.objects.create(
                username="member_a", email="member_a@example.com"
            ),
            "user_a": User.objects.create(
                username="user_a", email="user_a@example.com"
            ),
        }
        self.workspace = Workspace.objects.create(title="test workspace")
        self.workspace2 = Workspace.objects.create(title="test workspace2")
        self.invitation = Invitation.objects.create(
            object_uuid=self.workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="invited@example.com",
        )

        # make the admin user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin"],
            role=WS_ADMIN,
        )
        # make the member_a user member of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
        )
        # make the member_a user member of the workspace2
        self.member_profile2 = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace2.uuid,
            user=self.users["member_a"],
            role=WS_MEMBER,
            name="name2",
        )

    def test_retrieve_invite_as_anonymous(self):
        """Anonymous users need to send the token to retrieve an invite."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        response = self.client.get(
            url, {"token": PersonSerializer(self.invitation).generate_token()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.invitation.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_retrieve_invite_as_anonymous_no_token(self):
        """With no token, invites are not available to anonymous users."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_invite_with_token(self):
        """Authenticated users can retrieve an invite with a valid token."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            url, {"token": PersonSerializer(self.invitation).generate_token()}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.invitation.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_retrieve_invite_with_no_token_fails(self):
        """Authenticated need a token to retrieve an invite."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_retrieve_invite_as_member(self):
        """A member can see existing invitations from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.invitation.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_retrieve_invite_as_admin(self):
        """An admin can see existing invitations from a workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            {"short_uuid": self.invitation.short_uuid}.items()
            <= dict(response.data).items()
        )

    def test_create_invite(self):
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"email": "anna_test@askanna.dev"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            {"email": "anna_test@askanna.dev"}.items() <= dict(response.data).items()
        )

    def test_create_double_invite_not_possible(self):
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"email": "invited@example.com"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_invite_active_member(self):
        """An invitation to an email of an existing member can not be created."""
        profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(url, {"email": profile.user.email}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_invite_removed_member(self):
        """An invitation to an email of a soft-deleted profile can be created."""
        profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
            deleted=timezone.now(),
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(url, {"email": profile.user.email}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_admin_can_revoke_invite(self):
        """Admins of a workspace can revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Invitation.objects.filter(uuid=self.invitation.uuid).exists())

    def test_member_can_revoke_invite(self):
        """Members of a workspace can revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Invitation.objects.filter(uuid=self.invitation.uuid).exists())

    def test_non_member_can_not_revoke_invite(self):
        """Non members of a workspace can not revoke an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Invitation.objects.filter(uuid=self.invitation.uuid).exists())

    def test_admin_can_not_revoke_invitation_from_other_workspace(self):
        """Revoking an invitation is limited to workspaces a user is member of."""
        extra_workspace = Workspace.objects.create(title="extra test workspace")
        extra_invitation = Invitation.objects.create(
            object_uuid=extra_workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="extra@example.com",
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": extra_workspace.short_uuid,
                "short_uuid": extra_invitation.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Invitation.objects.filter(uuid=self.invitation.uuid).exists())

    @override_settings(ASKANNA_INVITATION_VALID_HOURS=0)
    def test_invite_token_expired(self):
        """An expired token is not good for accepting an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["token"][0], "Token expired")

    def test_create_invite_not_as_non_member(self):
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"email": "anna_test@askanna.dev"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_accept_invite(self):
        """After accepting an invite, a new Profile exists."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertQuerysetEqual(Invitation.objects.filter(pk=self.invitation.pk), [])

        profile = UserProfile.objects.get(pk=self.invitation.pk)
        self.assertEqual(profile.user, self.users["user_a"])
        self.assertEqual(profile.object_uuid, self.workspace.uuid)

    def test_member_cannot_accept_invite(self):
        """An existing member can not accept an invite to the same workspace."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("user", response.data)
        self.assertEqual(
            response.data["user"][0], "User is already part of this workspace"
        )

    def test_accept_invite_with_deleted_profile(self):
        """An invite can be accepted by a user with a soft-deleted profile."""
        UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_a"],
            deleted=timezone.now(),
        )

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_invite_requires_authentication(self):
        """An anonymous user can not accept an invite."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        response = self.client.patch(url, {}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_accept_invite_token_validated(self):
        """A token error is returned on invalid token."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url, {"status": "accepted", "token": "fake_token",}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["token"][0], "Token is not valid")

    def test_accept_invite_token_is_required(self):
        """A missing token error is returned when token is missing."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"status": "accepted",}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        self.assertEqual(
            response.data["token"][0], "Token is required when accepting invitation"
        )

    def test_accept_invite_fails_on_profile(self):
        """Accepting an already accepted invitation (a Profile) fails."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_profile.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.member_profile).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["token"][0], "Token is already used")

    def test_accept_invite_with_token_for_wrong_invitation_fails(self):
        """Accepting an already accepted invitation (a Profile) fails."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        to_fail_invitation = Invitation.objects.create(
            object_uuid=self.workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="will_fail@example.com",
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(to_fail_invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("token", response.data)

    def test_accept_invite_for_wrong_workspace_fails(self):
        """The invitation must be for the correct workspace."""
        to_fail_workspace = Workspace.objects.create(title="will fail workspace")

        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": to_fail_workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {
                "status": "accepted",
                "token": PersonSerializer(self.invitation).generate_token(),
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_limited_to_current_workspace(self):
        """Listing of people is correctly filtered to requested workspace."""
        new_workspace = Workspace.objects.create(title="test workspace")
        filtered_invitation = Invitation.objects.create(
            object_uuid=new_workspace.uuid,
            object_type=MSP_WORKSPACE,
            email="invited@example.com",
        )

        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(url,)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        uuids = [p["uuid"] for p in response.data]
        self.assertEqual(len(uuids), 3)
        self.assertNotIn(str(filtered_invitation.pk), uuids)
        self.assertIn(str(self.invitation.pk), uuids)
        self.assertIn(str(self.member_profile.pk), uuids)

    def test_invitation_data_is_not_writable(self):
        """Data from an invitation is read only once it has been created."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            url,
            {"email": "invalid", "object_uuid": "invalid", "object_type": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "invited@example.com")
        self.assertEqual(response.data["object_uuid"], str(self.workspace.uuid))
        self.assertEqual(response.data["object_type"], MSP_WORKSPACE)

    def test_non_member_can_not_modify_invitation(self):
        """An non member can not modify an invitation."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["user_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"email": "new@example.com"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_creating_invite_sends_invitation_email(self):
        """After creating an invitation, an invitation email is sent."""
        url = reverse(
            "workspace-people-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"email": "anna_test@askanna.dev"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(
            mail.outbox[0].subject,
            f"You’re invited to join {self.workspace} on AskAnna",
        )

    def test_modifying_invite_resends_invitation_email(self):
        """After modifying an invitation, an invitation email is sent again."""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.invitation.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"status": "invited"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(
            mail.outbox[0].subject,
            f"You’re invited to join {self.workspace} on AskAnna",
        )

    def test_modify_membership_name(self):
        """Change the name in the membership"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_profile.short_uuid,
            },
        )

        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "new-name",}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], "new-name")

    def test_modify_membership_name_should_not_affect_other_workspace_profiles(self):
        """Change the name in the membership"""
        url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_profile.short_uuid,
            },
        )

        url2 = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace2.short_uuid,
                "short_uuid": self.member_profile2.short_uuid,
            },
        )
        token = self.users["member_a"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(url, {"name": "new-name",}, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], "new-name")

        response = self.client.patch(url2, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertEqual(response.data["name"], "name2")
