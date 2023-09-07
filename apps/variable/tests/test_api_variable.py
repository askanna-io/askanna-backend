import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from core.tests.base import BaseUserPopulation
from variable.models import Variable

pytestmark = pytest.mark.django_db


class BaseProjectVariable(BaseUserPopulation, APITestCase):
    def setUp(self):
        super().setUp()
        self.variables = {
            "variable": Variable.objects.create(
                name="TestVariable",
                value="TestValue",
                is_masked=False,
                project=self.projects["project_a_wp_private_pr_private"],
            ),
            "variable_masked": Variable.objects.create(
                name="TestVariableMasked",
                value="TestMaskedValue",
                is_masked=True,
                project=self.projects["project_a_wp_private_pr_private"],
            ),
            "variable_other_project": Variable.objects.create(
                name="TestVariableOtherProject",
                value="TestOtherProjectValue",
                is_masked=False,
                project=self.projects["project_a_wp_private_pr_public"],
            ),
            "variable_public": Variable.objects.create(
                name="TestVariablePublic",
                value="TestPublicValue",
                is_masked=False,
                project=self.projects["project_c_wp_public_pr_public"],
            ),
            "variable_public_masked": Variable.objects.create(
                name="TestVariablePublicMasked",
                value="TestPublicMaskedValue",
                is_masked=True,
                project=self.projects["project_c_wp_public_pr_public"],
            ),
            "variable_wp_public_pr_private": Variable.objects.create(
                name="TestVariableWPPublicPRPrivate",
                value="TestWPPublicPRPrivateValue",
                is_masked=False,
                project=self.projects["project_c_wp_public_pr_private"],
            ),
        }

    def tearDown(self):
        super().tearDown()
        for variable in self.variables.values():
            variable.delete()


class TestVariableListAPI(BaseProjectVariable):
    """
    Testing the list function for the /v1/variable/
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "variable-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_anna(self):
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_admin(self):
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5  # type: ignore

    def test_list_as_member(self):
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 5  # type: ignore

    def test_list_as_nonmember(self):
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_anonymous(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_filter_by_project(self):
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            {"project_suuid": self.projects["project_a_wp_private_pr_private"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_filter_by_workspace(self):
        self.activate_user("admin")
        response = self.client.get(
            self.url,
            {"workspace_suuid": self.workspaces["workspace_a"].suuid},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3  # type: ignore


class TestVariableDetailAPI(BaseProjectVariable):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "suuid": self.variables["variable"].suuid},
        )
        self.url_for_masked_var = reverse(
            "variable-detail",
            kwargs={"version": "v1", "suuid": self.variables["variable_masked"].suuid},
        )

    def test_detail_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_admin(self):
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] == "TestValue"  # type: ignore

    def test_detail_as_admin_masked_variable(self):
        self.activate_user("admin")
        response = self.client.get(self.url_for_masked_var)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "TestVariableMasked"  # type: ignore
        assert response.data["value"] == "***masked***"  # type: ignore

    def test_detail_as_member(self):
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] == "TestValue"  # type: ignore

    def test_detail_as_member_maskedvariable(self):
        self.activate_user("member")
        response = self.client.get(self.url_for_masked_var)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "TestVariableMasked"  # type: ignore
        assert response.data["value"] == "***masked***"  # type: ignore

    def test_detail_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_detail_as_anonymous(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestVariableCreateAPI(BaseProjectVariable):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "variable-list",
            kwargs={"version": "v1"},
        )

    def test_create_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_as_admin(self):
        self.activate_user("admin")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "value": "TestValue",
                "is_masked": False,
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] == "TestValue"  # type: ignore

    def test_create_as_member(self):
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariableMasked",
                "value": "TestValueMasked",
                "is_masked": True,
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TestVariableMasked"  # type: ignore
        assert response.data["value"] == "***masked***"  # type: ignore

    def test_create_as_member_empty_value(self):
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "value": "",
                "is_masked": False,
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] == ""  # type: ignore

    def test_create_as_member_empty_value_masked(self):
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "value": "",
                "is_masked": True,
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] == "***masked***"  # type: ignore

    def test_create_as_member_no_value(self):
        self.activate_user("member")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == "TestVariable"  # type: ignore
        assert response.data["value"] is None  # type: ignore

    def test_create_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_create_as_anonymous(self):
        response = self.client.post(
            self.url,
            {
                "name": "TestVariable",
                "project_suuid": self.projects["project_a_wp_private_pr_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestVariableChangeAPI(BaseProjectVariable):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "suuid": self.variables["variable"].suuid},
        )

    def test_change_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "newvalue",
                "is_masked": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_change_as_admin(self):
        self.activate_user("admin")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "newvalue",
                "is_masked": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "newname"  # type: ignore
        assert response.data["value"] == "newvalue"  # type: ignore
        assert response.data["created_at"] != response.data["modified_at"]  # type: ignore

    def test_change_as_member(self):
        self.activate_user("member")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "newvalue",
                "is_masked": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "newname"  # type: ignore
        assert response.data["value"] == "***masked***"  # type: ignore
        assert response.data["created_at"] != response.data["modified_at"]  # type: ignore

    def test_change_as_member_empty_value(self):
        self.activate_user("member")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "",
                "is_masked": False,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "newname"  # type: ignore
        assert response.data["value"] == ""  # type: ignore
        assert response.data["created_at"] != response.data["modified_at"]  # type: ignore

    def test_change_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "newvalue",
                "is_masked": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_change_as_anonymous(self):
        response = self.client.patch(
            self.url,
            {
                "name": "newname",
                "value": "newvalue",
                "is_masked": True,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestVariableDeleteAPI(BaseProjectVariable):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "variable-detail",
            kwargs={"version": "v1", "suuid": self.variables["variable"].suuid},
        )

    def test_delete_as_askanna_admin(self):
        self.activate_user("anna")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_admin(self):
        self.activate_user("admin")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_member(self):
        self.activate_user("member")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_as_non_member(self):
        self.activate_user("non_member")
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_as_anonymous(self):
        response = self.client.delete(self.url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
