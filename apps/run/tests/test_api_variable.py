from django.urls import reverse
from rest_framework import status

from run.tests.base import BaseAPITestRun


class TestTrackedVariablesListAPI(BaseAPITestRun):
    """
    Test to list the Tracked Variables
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_variables["run_2"].suuid,
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We can list tracked variables as AskAnna admin,
        but response will be empty because of not having access to this workspace.
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        """
        We can list trackedvariables as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_member(self):
        """
        We can list trackedvariables as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

    def test_list_as_non_member(self):
        """
        We can list tracked variables as non_member of a workspace,
        but response will be empty because of not having access to this workspace.
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        """
        We can list tracked variables as anonymous,
        but response will be empty because of not having access to this workspace.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_member_order_by_variable_name(self):
        """
        We get detail tracked variables as member of a workspace and order them by variable name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "order_by": "variable.name",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4

        response_reversed = self.client.get(
            self.url,
            {
                "order_by": "-variable.name",
            },
        )
        assert response_reversed.status_code == status.HTTP_200_OK
        assert len(response_reversed.data["results"]) == 4

        assert (
            response.data["results"][0]["variable"]["name"] == response_reversed.data["results"][3]["variable"]["name"]
        )

    def test_list_as_member_filter_variable_name(self):
        """
        We test the filter by variable name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"variable_name": "Accuracy"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_variable_filter_label_name(self):
        """
        We test the filter by label name
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {"label_name": "product"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4


class TestTrackedVariablesPublicProjectListAPI(BaseAPITestRun):
    """
    Test to list the Tracked Variables from a job in a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_variables["run_4"].suuid,
            },
        )

    def test_list_as_non_member(self):
        """
        Public project run variables are listable by anyone
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_anonymous(self):
        """
        Public project run variables are listable by anyone
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2


class TestVariablesUpdateAPI(BaseAPITestRun):
    """
    We update the variables of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.run_variables["run_2"].suuid,
                "run__suuid": self.run_variables["run_2"].suuid,
            },
        )

    def test_update_as_askanna_admin(self):
        """
        We cannot update variables as AskAnna admin that is not member of a workspace
        """
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.patch(
            self.url,
            {"variables": self.variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_admin(self):
        """
        We update variables as admin of a workspace
        """
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.patch(
            self.url,
            {"variables": self.variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_update_as_member(self):
        """
        We update variables as member of a workspace
        """
        self.set_authorization(self.users["workspace_member"])

        response = self.client.patch(
            self.url,
            {"variables": self.variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None

    def test_update_as_non_member(self):
        """
        We cannot update variables as non-member of a workspace
        """
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.patch(
            self.url,
            {"variables": self.variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_anonymous(self):
        """
        We cannot variables metrics as anonymous
        """
        response = self.client.patch(
            self.url,
            {"variables": self.variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
