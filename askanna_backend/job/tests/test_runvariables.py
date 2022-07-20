from django.urls import reverse
from job.models import JobRun, RunVariableRow, RunVariables
from job.tasks.variables import post_run_deduplicate_variables
from rest_framework import status
from rest_framework.test import APITestCase

from .base import (
    BaseJobTestDef,
    tracked_variables_response_good,
    variable_response_good_small,
)


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


class TestRunVariablesDeduplicate(BaseJobTestDef, APITestCase):
    def setUp(self):
        super().setUp()
        self.jobrun_deduplicate = JobRun.objects.create(
            name="deduplicate",
            description="test deduplicate",
            package=self.package,
            jobdef=self.jobdef,
            status="COMPLETED",
            owner=self.users.get("member"),
            member=self.members.get("member"),
            run_image=self.run_image,
            duration=123,
        )

        self.variables_to_test_deduplicate = [
            {
                "run_suuid": self.jobrun_deduplicate.short_uuid,
                "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
                "created": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": self.jobrun_deduplicate.short_uuid,
                "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
                "created": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

        self.run_variables_deduplicate = RunVariables.objects.get(jobrun=self.jobrun_deduplicate)
        self.run_variables_deduplicate.variables = self.variables_to_test_deduplicate
        self.run_variables_deduplicate.save()

    def test_run_variables_deduplicate(self):
        #  Count variables before adding duplicates
        variables = RunVariableRow.objects.filter(run_suuid=self.jobrun_deduplicate.short_uuid)
        self.assertEqual(len(variables), 2)
        variable_record = RunVariables.objects.get(uuid=self.run_variables_deduplicate.uuid)
        self.assertEqual(variable_record.count, 2)

        # Add duplicate variables
        for variable in self.variables_to_test_deduplicate:
            RunVariableRow.objects.create(
                project_suuid=self.jobrun_deduplicate.jobdef.project.short_uuid,
                job_suuid=self.jobrun_deduplicate.jobdef.short_uuid,
                run_suuid=self.jobrun_deduplicate.short_uuid,
                variable=variable["variable"],
                label=variable["label"],
                created=variable["created"],
            )
        self.run_variables_deduplicate.update_meta()

        variables_with_duplicates = RunVariableRow.objects.filter(run_suuid=self.jobrun_deduplicate.short_uuid)
        self.assertEqual(len(variables_with_duplicates), 4)
        variable_record_with_duplicates = RunVariables.objects.get(uuid=self.run_variables_deduplicate.uuid)
        self.assertEqual(variable_record_with_duplicates.count, 4)

        # Dedepulicate run metric records
        post_run_deduplicate_variables(self.jobrun_deduplicate.short_uuid)

        variables_after_deduplicates = RunVariableRow.objects.filter(run_suuid=self.jobrun_deduplicate.short_uuid)
        self.assertEqual(len(variables_after_deduplicates), 2)

        # Deduplicate should also update the main metrics count
        variable_record_after_deduplicate = RunVariables.objects.get(uuid=self.run_variables_deduplicate.uuid)
        self.assertEqual(variable_record_after_deduplicate.count, 2)

    def tearDown(self):
        super().tearDown()
        self.jobrun_deduplicate.delete()
