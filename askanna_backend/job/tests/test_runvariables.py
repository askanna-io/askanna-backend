# -*- coding: utf-8 -*-
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import (
    BaseJobTestDef,
    variable_response_good_small,
)


class TestTrackedVariablesListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Tracked Variables
    """

    def setUp(self):
        self.url = reverse(
            "run-variables-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run_suuid": self.tracked_variables.get(
                    "run1"
                ).short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list trackedvariables as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

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
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        We can list trackedvariables as nonmember of a workspace, but response will be empty because of not having access to this workspace.
        """
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_anonymous(self):
        """
        We can list trackedvariables as member of a workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_list_as_member_order_by_variablename(self):
        """
        We get detail trackedvariables as member of a workspace,
        but request the trackedvariables to be returned in reversed sort on name
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

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
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

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
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        query_params = {"label_name": "product"}

        response = self.client.get(
            self.url,
            query_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)


class TestVariablesMetaAPI(BaseJobTestDef, APITestCase):
    """
    Test to get meta on specific variables for a jobrun
    """

    def setUp(self):
        self.url = reverse(
            "run-variables-meta",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.tracked_variables.get(
                    "run1"
                ).short_uuid,
                "jobrun__short_uuid": self.tracked_variables.get("run1").short_uuid,
            },
        )

    def test_meta_as_member(self):
        """
        Retrieve the meta information about the metrics
        """
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.get(
            self.url,
            format="json",
            HTTP_HOST="testserver",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestVariablesUpdateAPI(BaseJobTestDef, APITestCase):
    """
    We update the variables of a run
    """

    def setUp(self):
        self.url = reverse(
            "run-variables-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_jobrun__short_uuid": self.tracked_variables.get(
                    "run1"
                ).short_uuid,
                "jobrun__short_uuid": self.tracked_variables.get("run1").short_uuid,
            },
        )

    def test_update_as_admin(self):
        """
        We update variables as admin of a workspace
        """
        token = self.users["admin"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

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
        token = self.users["user"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

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
        token = self.users["user_nonmember"].auth_token
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_as_anonymous(self):
        """
        We cannot variables metrics as anonymous
        """
        response = self.client.patch(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
