import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, UserProfile
from workspace.models import Workspace

from .test_global_me import (
    BaseTestGlobalMeDelete,
    BaseTestGlobalMeGet,
    BaseTestGlobalMePatch,
)

pytestmark = pytest.mark.django_db


class WorkspaceTestSet:
    def setUp(self):
        super().setUp()
        self.workspace = Workspace.objects.create(name="test workspace")
        self.workspace_public = Workspace.objects.create(
            name="test workspace public",
            visibility="PUBLIC",
        )

        # make the admin_a user member of the workspace
        self.admin_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["admin"],
            role=WS_ADMIN,
            name="name of admin in membership",
            job_title="job_title of admin in membership",
        )
        # make the member user member of the workspace
        self.member_profile = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user"],
            role=WS_MEMBER,
            name="name of member in membership",
            job_title="job_title of member in membership",
        )

        # make the member_b user member of the workspace
        self.member_profile_b = UserProfile.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=self.workspace.uuid,
            user=self.users["user_b"],
            role=WS_MEMBER,
            name="name of member_b in membership",
            job_title="job_title of member_b in membership",
            use_global_profile=False,
        )

        self.url = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "short_uuid": self.workspace.short_uuid,
            },
        )

        self.url_non_exist = reverse(
            "workspace-me",
            kwargs={
                "version": "v1",
                "short_uuid": self.workspace.short_uuid[:-1] + "1",
            },
        )


class TestWorkspaceMeGet(WorkspaceTestSet, BaseTestGlobalMeGet, APITestCase):
    def test_me_as_anna(self):
        """
        Anna doesn't have acces to the workspace
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_as_user_non_exist_workspace(self):
        """
        As an user of a certain workspace, we just get `global.member` on global level
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url_non_exist,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_as_anonymous(self):
        """
        An anonymous user cannot get /me on a private workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestWorkspaceMeDelete(WorkspaceTestSet, BaseTestGlobalMeDelete, APITestCase):
    def test_me_as_anna(self):
        """
        Anna is not a member and not admin, so not allowed to delete the workspace membership (which doesn't exist)
        """
        token = self.users["anna"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_me_as_anonymous(self):
        """
        Anonymous cannot delete /me
        """
        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_me_as_member_delete_user_copies_global_profile_data_to_membership(self):
        """
        On deleting a user via /me .. we should update the UserProfile
        This test is 2 sided:
        - delete the user via /me (as user)
        - check the membership profile in database (refresh object first)
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        url = reverse(
            "global-me",
            kwargs={
                "version": "v1",
            },
        )

        response = self.client.delete(
            url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # then check the details of the membership via django
        self.member_profile.refresh_from_db()

        # the following values are coming from the global user
        self.assertEqual(self.member_profile.name, "user")
        self.assertEqual(self.member_profile.job_title, "Job Title user")

        # the following values are set on creating the UserProfile/Membership
        # and should not found in the member_profile anymore
        self.assertNotEqual(self.member_profile.name, "name of member in membership")
        self.assertNotEqual(self.member_profile.job_title, "job_title of member in membership")

    def test_me_as_member_delete_membership_copied_global_profile_to_membership(self):
        """
        Deleting own membership, same behaviour as deleting /me
        """

        # the following values are set on creating the UserProfile/Membership
        # Should find this before deleting the membership profile
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.name, "name of member in membership")
        self.assertEqual(self.member_profile.job_title, "job_title of member in membership")

        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # then check the details of the membership via django
        self.member_profile.refresh_from_db()

        # the following values are coming from the global user
        self.assertEqual(self.member_profile.name, "user")
        self.assertEqual(self.member_profile.job_title, "Job Title user")

        # the following values are set on creating the UserProfile/Membership
        # and should not found in the member_profile anymore
        self.assertNotEqual(self.member_profile.name, "name of member in membership")
        self.assertNotEqual(self.member_profile.job_title, "job_title of member in membership")

    def test_me_as_member_delete_membership_NO_copy_global_profile_to_membership(self):
        """
        Deleting own membership, same behaviour as deleting /me
        NOT using use_global_profile
        """

        # the following values are set on creating the UserProfile/Membership
        # Should find this before deleting the membership profile
        self.member_profile_b.refresh_from_db()
        self.assertEqual(self.member_profile_b.name, "name of member_b in membership")
        self.assertEqual(self.member_profile_b.job_title, "job_title of member_b in membership")

        token = self.users["user_b"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # then check the details of the membership via django
        self.member_profile_b.refresh_from_db()

        # the following values are coming from the global user
        # should not be found here
        self.assertNotEqual(self.member_profile_b.name, "user_b")
        self.assertNotEqual(self.member_profile_b.job_title, "Job Title user_b")

        # the following values are set on creating the UserProfile/Membership
        # and should still be found in the member_profile
        self.assertEqual(self.member_profile_b.name, "name of member_b in membership")
        self.assertEqual(self.member_profile_b.job_title, "job_title of member_b in membership")

    def test_me_as_admin_delete_membership_copied_global_profile_to_membership(self):
        """
        Deleting membership via workspace/people by a workspace admin user
        """

        # the following values are set on creating the UserProfile/Membership
        # Should find this before deleting the membership profile
        self.member_profile.refresh_from_db()
        self.assertEqual(self.member_profile.name, "name of member in membership")
        self.assertEqual(self.member_profile.job_title, "job_title of member in membership")

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        delete_url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_profile.short_uuid,
            },
        )
        response = self.client.delete(
            delete_url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # then check the details of the membership via django
        self.member_profile.refresh_from_db()

        # the following values are coming from the global user
        self.assertEqual(self.member_profile.name, "user")
        self.assertEqual(self.member_profile.job_title, "Job Title user")

        # the following values are set on creating the UserProfile/Membership
        # and should not found in the member_profile anymore
        self.assertNotEqual(self.member_profile.name, "name of member in membership")
        self.assertNotEqual(self.member_profile.job_title, "job_title of member in membership")

    def test_me_as_admin_delete_membership_NO_copy_global_profile_to_membership(self):
        """
        Deleting membership via workspace/people by a workspace admin user
        Should not update the membership as use_global_profile is False
        """

        # the following values are set on creating the UserProfile/Membership
        # Should find this before deleting the membership profile
        self.member_profile_b.refresh_from_db()
        self.assertEqual(self.member_profile_b.name, "name of member_b in membership")
        self.assertEqual(self.member_profile_b.job_title, "job_title of member_b in membership")

        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)
        delete_url = reverse(
            "workspace-people-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_workspace__short_uuid": self.workspace.short_uuid,
                "short_uuid": self.member_profile_b.short_uuid,
            },
        )
        response = self.client.delete(
            delete_url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # then check the details of the membership via django
        self.member_profile_b.refresh_from_db()

        # the following values are coming from the global user
        # should not be found here
        self.assertNotEqual(self.member_profile_b.name, "user_b")
        self.assertNotEqual(self.member_profile_b.job_title, "Job Title user_b")

        # the following values are set on creating the UserProfile/Membership
        # and should still be found in the member_profile
        self.assertEqual(self.member_profile_b.name, "name of member_b in membership")
        self.assertEqual(self.member_profile_b.job_title, "job_title of member_b in membership")


class TestWorkspaceMePatch(WorkspaceTestSet, BaseTestGlobalMePatch, APITestCase):
    def test_me_as_anna(self):
        """
        Test for anna is not needed as anna doesn't have a profile in a workspace
        """
        pass

    def test_member_set_use_global_profile(self):
        """
        When use_global_profile is set, use the details from the global profile
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "use_global_profile": True,
                "name": "some random name that is not used",
                "job_title": "some random job_title that is not used",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # the fields stored in membership itself, but not reflected in effective name
        self.assertEqual(response.data.get("name"), "some random name that is not used")
        self.assertEqual(response.data.get("job_title"), "some random job_title that is not used")
        self.assertEqual(response.data.get("use_global_profile"), True)

        # the effective name and job_title
        self.assertEqual(response.data.get("membership", {}).get("name"), "user")
        self.assertEqual(response.data.get("membership", {}).get("job_title"), "Job Title user")

        # how do i look like? do another get on the workspace/me
        response_get = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # the fields stored in membership itself, but not reflected in effective name
        self.assertEqual(response_get.data.get("name"), "some random name that is not used")
        self.assertEqual(response_get.data.get("job_title"), "some random job_title that is not used")
        self.assertEqual(response_get.data.get("use_global_profile"), True)

        # the effective name and job_title
        self.assertEqual(response_get.data.get("membership", {}).get("name"), "user")
        self.assertEqual(response_get.data.get("membership", {}).get("job_title"), "Job Title user")

    def test_member_set_not_use_global_profile(self):
        """
        When use_global_profile is set, use the details from the global profile
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {
                "use_global_profile": False,
                "name": "some random name that is not used",
                "job_title": "some random job_title that is not used",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # the fields stored in membership itself, but not reflected in effective name
        self.assertEqual(response.data.get("name"), "some random name that is not used")
        self.assertEqual(response.data.get("job_title"), "some random job_title that is not used")
        self.assertEqual(response.data.get("use_global_profile"), False)

        # the effective name and job_title
        self.assertEqual(
            response.data.get("membership", {}).get("name"),
            "some random name that is not used",
        )
        self.assertEqual(
            response.data.get("membership", {}).get("job_title"),
            "some random job_title that is not used",
        )

        # how do i look like? do another get on the workspace/me
        response_get = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response_get.status_code, status.HTTP_200_OK)

        # the fields stored in membership itself, but not reflected in effective name
        self.assertEqual(response_get.data.get("name"), "some random name that is not used")
        self.assertEqual(response_get.data.get("job_title"), "some random job_title that is not used")
        self.assertEqual(response_get.data.get("use_global_profile"), False)

        # the effective name and job_title
        self.assertEqual(
            response_get.data.get("membership", {}).get("name"),
            "some random name that is not used",
        )
        self.assertEqual(
            response_get.data.get("membership", {}).get("job_title"),
            "some random job_title that is not used",
        )

    def test_me_as_anonymous(self):
        """
        Anonymous cannot update workspace/me
        """
        update_me_payload = {
            "name": "new name",
            "job_title": "new title",
        }

        response = self.client.patch(
            self.url,
            update_me_payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
