import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from job.models import JobVariable
from project.models import Project
from users.models import MSP_WORKSPACE, WS_ADMIN, WS_MEMBER, Membership, User
from workspace.models import Workspace

pytestmark = pytest.mark.django_db


class BaseVariables:
    @classmethod
    def setup_class(cls):
        cls.users = {
            "admin": User.objects.create(
                username="admin",
                is_staff=True,
                is_superuser=True,
                email="admin@askanna.dev",
            ),
            "user": User.objects.create(username="user", email="user@askanna.dev"),
            "user_nonmember": User.objects.create(
                username="user_nonmember", email="user_nonmember@askanna.dev"
            ),
        }

        # setup variables
        cls.workspace = Workspace.objects.create(**{"title": "WorkspaceX",})
        cls.project = Project.objects.create(
            **{"name": "TestProject", "workspace": cls.workspace}
        )
        cls.variable = JobVariable.objects.create(
            **{
                "name": "TestVariable",
                "value": "TestValue",
                "is_masked": False,
                "project": cls.project,
            }
        )

        cls.variable_masked = JobVariable.objects.create(
            **{
                "name": "TestVariableMasked",
                "value": "TestValue",
                "is_masked": True,
                "project": cls.project,
            }
        )

        # make the admin user member of the workspace
        admin_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["admin"],
            role=WS_ADMIN,
        )
        # make the memberA user member of the workspace
        memberA_member = Membership.objects.create(
            object_type=MSP_WORKSPACE,
            object_uuid=cls.workspace.uuid,
            user=cls.users["user"],
            role=WS_MEMBER,
        )

    @classmethod
    def teardown_class(cls):
        """
        Remove all the user instances we had setup for the test
        """
        for _, user in cls.users.items():
            user.delete()
        cls.variable.delete()
        cls.variable_masked.delete()


class TestVariableCreateAPI(BaseVariables, APITestCase):
    """
    Testing the delete function for the /v1/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse("variable-list", kwargs={"version": "v1"},)
        self.tmp_variable = None

    def tearDown(self):
        if self.tmp_variable:
            JobVariable.objects.get(short_uuid=self.tmp_variable).delete()

    def test_create_as_admin(self):
        """
        We can create variables as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_token = {
            "name": "TestVariable",
            "value": "TestValue",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.tmp_variable = response.data.get("short_uuid")
        self.assertTrue(response.data.get("name") == "TestVariable")
        self.assertTrue(response.data.get("value") == "TestValue")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_member(self):
        """
        A normal user can create variable where he/she has access to as member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_token = {
            "name": "TestVariable",
            "value": "TestValue",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.tmp_variable = response.data.get("short_uuid")
        self.assertTrue(response.data.get("name") == "TestVariable")
        self.assertTrue(response.data.get("value") == "TestValue")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_member_empty_value(self):
        """
        A normal user can create variable where he/she has access to as member
        Testcase: empty value
        Expecting to raise a Validation error
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_token = {
            "name": "TestVariable",
            "value": "",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.tmp_variable = response.data.get("short_uuid")
        self.assertIn(b"cannot be empty", response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_as_member_blank_value(self):
        """
        A normal user can create variable where he/she has access to as member
        Testcase: blank value
        Expecting to pass
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_token = {
            "name": "TestVariable",
            "value": " ",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.tmp_variable = response.data.get("short_uuid")
        self.assertTrue(response.data.get("name") == "TestVariable")
        self.assertTrue(response.data.get("value") == " ")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_as_nonmember(self):
        """
        A normal user can not create variable as a nonmember of a workspace
        We expect a 403
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        new_token = {
            "name": "TestVariable",
            "value": "TestValue",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_as_anonymous(self):
        """
        We cannot list variables as anonymous user
        """
        new_token = {
            "name": "TestVariable",
            "value": "TestValue",
            "is_masked": False,
            "project": self.project.short_uuid,
        }

        response = self.client.post(self.url, new_token, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestVariableListAPI(BaseVariables, APITestCase):
    """
    Testing the list function for the /v1/variable/
    """

    def setUp(self):
        self.url = reverse("variable-list", kwargs={"version": "v1"},)

    def test_list_as_admin(self):
        """
        We can list variables as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertTrue(len(response.data) == 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_member(self):
        """
        A normal user can list variables where he/she has access to
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertTrue(len(response.data) == 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_nonmember(self):
        """
        A non member should not have access to the workspace and thus variables
        So an empty list should be returned
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.data, [])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_anonymous(self):
        """
        We cannot list variables as anonymous user
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestVariableDetailAPI(BaseVariables, APITestCase):
    """
    Testing the detail function for the /v1/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.urlformaskedvar = reverse(
            "variable-detail",
            kwargs={"version": "v1", "short_uuid": self.variable_masked.short_uuid},
        )
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "short_uuid": self.variable.short_uuid},
        )

    def test_detail_as_admin(self):
        """
        We can list variables as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "TestVariable")
        self.assertTrue(response.data.get("value") == "TestValue")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_admin_maskedvariable(self):
        """
        A normal user can list variables where he/she has access to as member
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.urlformaskedvar, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "TestVariableMasked")
        self.assertTrue(response.data.get("value") == "***masked***")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_member(self):
        """
        A normal user can list variables where he/she has access to as member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "TestVariable")
        self.assertTrue(response.data.get("value") == "TestValue")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_member_maskedvariable(self):
        """
        A normal user can list variables where he/she has access to as member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.urlformaskedvar, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "TestVariableMasked")
        self.assertTrue(response.data.get("value") == "***masked***")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_detail_as_nonmember(self):
        """
        A normal user can not list variables as a nonmember doesn't own
        We expect a 404 as this variable cannot be found by a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We cannot list variables as anonymous user
        """
        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestVariableChangeAPI(BaseVariables, APITestCase):
    """
    Testing the change (PUT/PATCH) function for the /v1/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "short_uuid": self.variable.short_uuid},
        )

    def test_change_as_admin(self):
        """
        We can list variables as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_var_payload = {
            "name": "newname",
            "value": "newvalue",
            "is_masked": True,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("value") == "newvalue")
        self.assertTrue(response.data.get("created") != response.data.get("modified"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_as_member(self):
        """
        A normal user can change variables where he/she has access to as member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_var_payload = {
            "name": "newname",
            "value": "newvalue",
            "is_masked": True,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("value") == "newvalue")
        self.assertTrue(response.data.get("created") != response.data.get("modified"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_as_member_empty_value(self):
        """
        A normal user can change variables where he/she has access to as member
        Also the value can be "blank", meaning, contain space only (non visible chars)
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_var_payload = {
            "name": "newname",
            "value": " ",
            "is_masked": False,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.assertTrue("short_uuid" in response.data.keys())
        self.assertTrue(response.data.get("name") == "newname")
        self.assertTrue(response.data.get("value") == " ")
        self.assertTrue(response.data.get("created") != response.data.get("modified"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_as_member_blank_value(self):
        """
        A normal user can change variables where he/she has access to as member
        Also the value can be "blank", meaning, contain space only (non visible chars)
        Testcase: blank values cannot be empty
        Expecting to fail validation
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_var_payload = {
            "name": "newname",
            "value": "",
            "is_masked": False,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.tmp_variable = response.data.get("short_uuid")
        self.assertIn(b"cannot be empty", response.content)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_as_nonmember(self):
        """
        A normal user can not change variables as a nonmember doesn't own
        We expect a 404 as this variable cannot be found by a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        change_var_payload = {
            "name": "newname",
            "value": "newvalue",
            "is_masked": True,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_as_anonymous(self):
        """
        We cannot change variables as anonymous user
        """
        change_var_payload = {
            "name": "newname",
            "value": "newvalue",
            "is_masked": True,
        }

        response = self.client.patch(self.url, change_var_payload, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestVariableDeleteAPI(BaseVariables, APITestCase):
    """
    Testing the delete function for the /v1/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "short_uuid": self.variable.short_uuid},
        )

    def test_delete_as_admin(self):
        """
        We can list variables as an admin user
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_member(self):
        """
        A normal user can list variables where he/she has access to as member
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_as_nonmember(self):
        """
        A normal user can not list variables as a nonmember doesn't own
        We expect a 404 as this variable cannot be found by a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.delete(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_anonymous(self):
        """
        We cannot list variables as anonymous user
        """
        response = self.client.delete(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# The same tests but on /v1/project/{{ short_uuid}}/variables/ level


class TestProjectVariableCreateAPI(TestVariableCreateAPI):
    """
    Testing the create function for the /v1/project/{{ project-short_uuid }}/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "project-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )
        self.tmp_variable = None


class TestProjectVariableListAPI(TestVariableListAPI):
    """
    Testing the list function for the /v1/project/{{ project-short_uuid }}/variable/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "project-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )

    def test_list_as_nonmember(self):
        """
        A non member should not have access to the workspace and thus variables
        We expect a 404 as this variable cannot be found by a non-member
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(self.url, format="json",)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestProjectVariableChangeAPI(TestVariableChangeAPI):
    """
    Testing the change function for the /v1/project/{{ project-short_uuid }}/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "project-variable-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.variable.short_uuid,
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )


class TestProjectVariableDetailAPI(TestVariableDetailAPI):
    """
    Testing the detail function for the /v1/project/{{ project-short_uuid }}/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "project-variable-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.variable.short_uuid,
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )
        self.urlformaskedvar = reverse(
            "project-variable-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.variable_masked.short_uuid,
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )


class TestProjectVariableDeleteAPI(TestVariableDeleteAPI):
    """
    Testing the delete function for the /v1/project/{{ project-short_uuid }}/{{ short_uuid }}
    """

    def setUp(self):
        self.url = reverse(
            "project-variable-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.variable.short_uuid,
                "parent_lookup_project__short_uuid": self.project.short_uuid,
            },
        )

