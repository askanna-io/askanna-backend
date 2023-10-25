from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import (
    BaseRunTest,
    tracked_variables_response_good,
    variable_response_good_small,
)
from run.models import Run, RunVariable, RunVariableMeta
from run.tasks.variable import post_run_deduplicate_variables


class TestRunVariableModel(BaseRunTest, APITestCase):
    """
    Test RunVariable model functions
    """

    def test_run_variables_function_load_from_file(self):
        assert self.tracked_variables["run1"].load_from_file() == tracked_variables_response_good

    def test_run_variables_function_update_meta_no_metrics_and_no_labels(self):
        modified_at_before = self.tracked_variables["run7"].modified_at
        self.tracked_variables["run7"].update_meta()
        assert self.tracked_variables["run7"].modified_at == modified_at_before
        assert self.tracked_variables["run7"].count == 0
        assert self.tracked_variables["run7"].size == 0
        assert self.tracked_variables["run7"].variable_names is None
        assert self.tracked_variables["run7"].label_names is None

    def test_run_variables_function_update_meta(self):
        modified_at_before_1 = self.tracked_variables["run7"].modified_at
        self.tracked_variables["run7"].update_meta()
        assert self.tracked_variables["run7"].modified_at == modified_at_before_1
        assert self.tracked_variables["run7"].count == 0
        assert self.tracked_variables["run7"].size == 0
        assert self.tracked_variables["run7"].variable_names is None
        assert self.tracked_variables["run7"].label_names is None

        self.tracked_variables["run7"].variables = tracked_variables_response_good
        self.tracked_variables["run7"].save()

        modified_at_before_2 = self.tracked_variables["run7"].modified_at
        self.tracked_variables["run7"].update_meta()
        assert self.tracked_variables["run7"].modified_at > modified_at_before_2
        assert self.tracked_variables["run7"].count == 4
        assert self.tracked_variables["run7"].size == 1210

        expected_variable_names = [
            {"name": "Accuracy", "type": "integer", "count": 2},
            {"name": "Quality", "type": "string", "count": 2},
        ]
        assert len(self.tracked_variables["run7"].variable_names) == 2  # type: ignore
        assert self.tracked_variables["run7"].variable_names[0] in expected_variable_names  # type: ignore
        assert self.tracked_variables["run7"].variable_names[1] in expected_variable_names  # type: ignore

        expected_label_names = [
            {"name": "city", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ]
        assert len(self.tracked_variables["run7"].label_names) == 3  # type: ignore
        assert self.tracked_variables["run7"].label_names[0] in expected_label_names  # type: ignore
        assert self.tracked_variables["run7"].label_names[1] in expected_label_names  # type: ignore
        assert self.tracked_variables["run7"].label_names[2] in expected_label_names  # type: ignore

    def test_run_variables_function_update_meta_no_labels(self):
        self.tracked_variables["run6"].update_meta()
        assert self.tracked_variables["run6"].count == 2
        assert self.tracked_variables["run6"].size == 344
        assert self.tracked_variables["run6"].variable_names is not None
        assert self.tracked_variables["run6"].label_names is None


class TestTrackedVariablesListAPI(BaseRunTest, APITestCase):
    """
    Test to list the Tracked Variables
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.tracked_variables["run1"].suuid,
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We can list tracked variables as AskAnna admin,
        but response will be empty because of not having access to this workspace.
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_admin(self):
        """
        We can list trackedvariables as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_as_member(self):
        """
        We can list trackedvariables as member of a workspace
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_as_non_member(self):
        """
        We can list tracked variables as non_member of a workspace,
        but response will be empty because of not having access to this workspace.
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_anonymous(self):
        """
        We can list tracked variables as anonymous,
        but response will be empty because of not having access to this workspace.
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_member_order_by_variable_name(self):
        """
        We get detail tracked variables as member of a workspace and order them by variable name
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            {
                "order_by": "variable.name",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

        response_reversed = self.client.get(
            self.url,
            {
                "order_by": "-variable.name",
            },
        )
        assert response_reversed.status_code == status.HTTP_200_OK
        assert len(response_reversed.data["results"]) == 4  # type: ignore

        assert (
            response.data["results"][0]["variable"]["name"]  # type: ignore
            == response_reversed.data["results"][3]["variable"]["name"]  # type: ignore
        )

    def test_list_as_member_filter_variable_name(self):
        """
        We test the filter by variable name
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"variable_name": "Accuracy"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_variable_filter_label_name(self):
        """
        We test the filter by label name
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"label_name": "product"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore


class TestTrackedVariablesPublicProjectListAPI(BaseRunTest, APITestCase):
    """
    Test to list the Tracked Variables from a job in a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.tracked_variables["run6"].suuid,
            },
        )

    def test_list_as_non_member(self):
        """
        Public project run variables are listable by anyone
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_anonymous(self):
        """
        Public project run variables are listable by anyone
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore


class TestVariablesUpdateAPI(BaseRunTest, APITestCase):
    """
    We update the variables of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-variable-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.tracked_variables["run1"].suuid,
                "run__suuid": self.tracked_variables["run1"].suuid,
            },
        )

    def test_update_as_askanna_admin(self):
        """
        We cannot update variables as AskAnna admin that is not member of a workspace
        """
        self.activate_user("anna")
        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

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
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None  # type: ignore

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
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None  # type: ignore

    def test_update_as_non_member(self):
        """
        We cannot update variables as non-member of a workspace
        """
        self.activate_user("non_member")
        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update_as_anonymous(self):
        """
        We cannot variables metrics as anonymous
        """
        response = self.client.patch(
            self.url,
            {"variables": variable_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestRunVariableDeduplicate(BaseRunTest, APITestCase):
    def setUp(self):
        super().setUp()
        self.run_deduplicate = Run.objects.create(
            name="deduplicate",
            description="test deduplicate",
            package=self.package,
            jobdef=self.jobdef,
            status="COMPLETED",
            created_by_user=self.users.get("member"),
            created_by_member=self.members.get("member"),
            run_image=self.run_image,
            duration=123,
        )

        self.variables_to_test_deduplicate = [
            {
                "run_suuid": self.run_deduplicate.suuid,
                "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": self.run_deduplicate.suuid,
                "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

        self.run_variables_deduplicate = RunVariableMeta.objects.get(run=self.run_deduplicate)
        self.run_variables_deduplicate.variables = self.variables_to_test_deduplicate
        self.run_variables_deduplicate.save()

    def test_run_variables_deduplicate(self):
        #  Count variables before adding duplicates
        variables = RunVariable.objects.filter(run=self.run_deduplicate)
        assert len(variables) == 2
        variable_record = RunVariableMeta.objects.get(uuid=self.run_variables_deduplicate.uuid)
        assert variable_record.count == 2

        # Add duplicate variables
        for variable in self.variables_to_test_deduplicate:
            RunVariable.objects.create(
                project_suuid=self.run_deduplicate.jobdef.project.suuid,
                job_suuid=self.run_deduplicate.jobdef.suuid,
                run_suuid=self.run_deduplicate.suuid,
                run=self.run_deduplicate,
                variable=variable["variable"],
                label=variable["label"],
                created_at=variable["created_at"],
            )
        self.run_variables_deduplicate.update_meta()

        variables_with_duplicates = RunVariable.objects.filter(run=self.run_deduplicate)
        assert len(variables_with_duplicates) == 4
        variable_record_with_duplicates = RunVariableMeta.objects.get(uuid=self.run_variables_deduplicate.uuid)
        assert variable_record_with_duplicates.count == 4

        # Dedepulicate run variable records
        post_run_deduplicate_variables(run_uuid=self.run_deduplicate.uuid)

        variables_after_deduplicates = RunVariable.objects.filter(run=self.run_deduplicate)
        assert len(variables_after_deduplicates) == 2
        variable_record_after_deduplicate = RunVariableMeta.objects.get(uuid=self.run_variables_deduplicate.uuid)
        assert variable_record_after_deduplicate.count == 2

    def tearDown(self):
        super().tearDown()
        self.run_deduplicate.delete()
