import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


from workspace.models import Workspace
from workspace.views import PersonViewSet
from users.models import Invitation, User, Membership, WS_MEMBER, WS_ADMIN

pytestmark = pytest.mark.django_db


class TestInviteSystem(APITestCase):
    @classmethod
    def setup_class(cls):
        cls.users = {
            "admin": User.objects.create(
                username="admin", is_staff=True, is_superuser=True
            ),
            "memberA": User.objects.create(username="memberA"),
            "userA": User.objects.create(username="memberB"),
        }
        cls.workspace = Workspace.objects.create(title="test workspace")

        # make the admin user member of the workspace
        admin_member = Membership.objects.create(
            object_type="WS",
            object_uuid=cls.workspace.uuid,
            user=cls.users["admin"],
            role=WS_ADMIN,
        )
        # make the memberA user member of the workspace
        memberA_member = Membership.objects.create(
            object_type="WS",
            object_uuid=cls.workspace.uuid,
            user=cls.users["memberA"],
            role=WS_MEMBER,
        )

    def test_create_invite(self):
        url = reverse(
            "workspace-invite-list",
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
            "workspace-invite-list",
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

        response = self.client.post(
            url, {"email": "anna_test@askanna.dev"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invite_not_as_non_member(self):
        url = reverse(
            "workspace-invite-list",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
            },
        )

        token = self.users["userA"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.post(
            url, {"email": "anna_test@askanna.dev"}, format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
