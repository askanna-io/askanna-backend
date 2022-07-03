# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef, variable_response_good_small, tracked_variables_response_good


class TestRunVariablesModel(BaseJobTestDef, APITestCase):
    """
    Test RunVariables model functions
    """

    def test_runvariables_function_load_from_file(self):
        self.assertEqual(self.tracked_variables["run1"].load_from_file(), tracked_variables_response_good)

    def test_runvariables_function_update_meta_no_metrics_and_no_labels(self):
        modified_before = self.tracked_variables["run7"].modified
        self.tracked_variables["run7"].update_meta()
        self.assertEqual(self.tracked_variables["run7"].modified, modified_before)

        self.assertEqual(self.tracked_variables["run7"].count, 0)
        self.assertEqual(self.tracked_variables["run7"].size, 0)
        self.assertIsNone(self.tracked_variables["run7"].variable_names)
        self.assertIsNone(self.tracked_variables["run7"].label_names)

    def test_runvariables_function_update_meta(self):
        modified_before_1 = self.tracked_variables["run7"].modified
        self.tracked_variables["run7"].update_meta()
        self.assertEqual(self.tracked_variables["run7"].modified, modified_before_1)

        self.assertEqual(self.tracked_variables["run7"].count, 0)
        self.assertEqual(self.tracked_variables["run7"].size, 0)
        self.assertIsNone(self.tracked_variables["run7"].variable_names)
        self.assertIsNone(self.tracked_variables["run7"].label_names)

        self.tracked_variables["run7"].variables = tracked_variables_response_good
        self.tracked_variables["run7"].save()

        modified_before_2 = self.tracked_variables["run7"].modified
        self.tracked_variables["run7"].update_meta()
        self.assertEqual(self.tracked_variables["run7"].modified, modified_before_2)

        self.assertEqual(self.tracked_variables["run7"].count, 4)
        self.assertEqual(self.tracked_variables["run7"].size, 1198)
        expected_variable_names = [
            {"name": "Accuracy", "type": "integer", "count": 2},
            {"name": "Quality", "type": "string", "count": 2},
        ]
        self.assertEqual(len(self.tracked_variables["run7"].variable_names), 2)
        self.assertIn(self.tracked_variables["run7"].variable_names[0], expected_variable_names)
        self.assertIn(self.tracked_variables["run7"].variable_names[1], expected_variable_names)
        expected_label_names = [
            {"name": "city", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ]
        self.assertEqual(len(self.tracked_variables["run7"].label_names), 3)
        self.assertIn(self.tracked_variables["run7"].label_names[0], expected_label_names)
        self.assertIn(self.tracked_variables["run7"].label_names[1], expected_label_names)
        self.assertIn(self.tracked_variables["run7"].label_names[2], expected_label_names)

    def test_runvariables_function_update_meta_no_labels(self):
        self.tracked_variables["run6"].update_meta()
        self.assertEqual(self.tracked_variables["run6"].count, 2)
        self.assertEqual(self.tracked_variables["run6"].size, 338)
        self.assertIsNotNone(self.tracked_variables["run6"].variable_names)
        self.assertIsNone(self.tracked_variables["run6"].label_names)


class TestTrackedVariablesListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Tracked Variables
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variables-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run_suuid": self.tracked_variables.get("run1").short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list trackedvariables as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member(self):
        """
        We can list trackedvariables as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        We can list trackedvariables as nonmember of a workspace,
        but response will be empty because of not having access to this workspace.
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_anonymous(self):
        """
        Anonymous user can list run variables from public projects only
        Not from this run (private project)
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_member_order_by_variablename(self):
        """
        We get detail trackedvariables as member of a workspace,
        but request the trackedvariables to be returned in reversed sort on name
        """
        self.activate_user("member")

        response = self.client.get(
            self.url + "?ordering=-variable.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

        response = self.client.get(
            self.url + "?ordering=variable.name",
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_variablename(self):
        """
        We test the filter by variable name
        """
        self.activate_user("member")

        query_params = {"variable_name": "Accuracy"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_list_as_variable_filter_labelname(self):
        """
        We test the filter by label name
        """
        self.activate_user("member")

        query_params = {"label_name": "product"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)


class TestTrackedVariablesPublicProjectListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Tracked Variables from a job in a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variables-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run_suuid": self.tracked_variables.get("run6").short_uuid,
            },
        )

    def test_list_as_nonmember(self):
        """
        Public project jobrun variables are listable by anyone
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_list_as_anonymous(self):
        """
        Public project jobrun variables are listable by anyone
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestVariablesUpdateAPI(BaseJobTestDef, APITestCase):
    """
    We update the variables of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variables-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.tracked_variables.get("run1").short_uuid,
                "jobrun__short_uuid": self.tracked_variables.get("run1").short_uuid,
            },
        )

    def test_update_as_admin(self):
        """
        We update variables as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, variable_response_good_small)

    def test_update_as_member(self):
        """
        We update variables as member of a workspace
        """
        self.activate_user("member")

        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, variable_response_good_small)

    def test_update_as_nonmember(self):
        """
        We cannot update variables as nonmember of a workspace
        """
        self.activate_user("non_member")

        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_as_anonymous(self):
        """
        We cannot variables metrics as anonymous
        """
        response = self.client.patch(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
