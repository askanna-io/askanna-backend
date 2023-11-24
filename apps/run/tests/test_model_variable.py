import pytest

from run.models import Run, RunVariable, RunVariableMeta
from run.tasks.variable import post_run_deduplicate_variables


class TestRunVariableModel:
    """
    Test RunVariable model functions
    """

    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_run_variables, variable_response_good):
        self.run_variables = test_run_variables
        self.variable_response_good = variable_response_good

    def test_run_variables_function_load_from_file(self):
        assert self.run_variables["run_2"].load_from_file() == self.variable_response_good

    def test_run_variables_function_update_meta_no_metrics_and_no_labels(self):
        modified_at_before = self.run_variables["run_3"].modified_at
        self.run_variables["run_3"].update_meta()
        assert self.run_variables["run_3"].modified_at == modified_at_before
        assert self.run_variables["run_3"].count == 0
        assert self.run_variables["run_3"].size == 0
        assert self.run_variables["run_3"].variable_names is None
        assert self.run_variables["run_3"].label_names is None

    def test_run_variables_function_update_meta(self):
        modified_at_before_1 = self.run_variables["run_3"].modified_at
        self.run_variables["run_3"].update_meta()
        assert self.run_variables["run_3"].modified_at == modified_at_before_1
        assert self.run_variables["run_3"].count == 0
        assert self.run_variables["run_3"].size == 0
        assert self.run_variables["run_3"].variable_names is None
        assert self.run_variables["run_3"].label_names is None

        self.run_variables["run_3"].variables = self.variable_response_good
        self.run_variables["run_3"].save()

        modified_at_before_2 = self.run_variables["run_3"].modified_at
        self.run_variables["run_3"].update_meta()
        assert self.run_variables["run_3"].modified_at > modified_at_before_2
        assert self.run_variables["run_3"].count == 4
        assert self.run_variables["run_3"].size == 1210

        expected_variable_names = [
            {"name": "Accuracy", "type": "integer", "count": 2},
            {"name": "Quality", "type": "string", "count": 2},
        ]
        assert len(self.run_variables["run_3"].variable_names) == 2
        assert self.run_variables["run_3"].variable_names[0] in expected_variable_names
        assert self.run_variables["run_3"].variable_names[1] in expected_variable_names

        expected_label_names = [
            {"name": "city", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ]
        assert len(self.run_variables["run_3"].label_names) == 3
        assert self.run_variables["run_3"].label_names[0] in expected_label_names
        assert self.run_variables["run_3"].label_names[1] in expected_label_names
        assert self.run_variables["run_3"].label_names[2] in expected_label_names

    def test_run_variables_function_update_meta_no_labels(self):
        self.run_variables["run_5"].update_meta()
        assert self.run_variables["run_5"].count == 2
        assert self.run_variables["run_5"].size == 344
        assert self.run_variables["run_5"].variable_names is not None
        assert self.run_variables["run_5"].label_names is None


class TestRunVariableDeduplicate:
    """
    Test RunVariable model functions to deduplicate variables
    """

    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_memberships, test_packages, test_jobs):
        self.memberships = test_memberships
        self.packages = test_packages
        self.jobs = test_jobs

        self.run_deduplicate = Run.objects.create(
            name="deduplicate",
            description="test deduplicate",
            package=self.packages["package_private_1"],
            jobdef=self.jobs["my-test-job"],
            status="COMPLETED",
            created_by_user=self.memberships["workspace_private_admin"].user,
            created_by_member=self.memberships["workspace_private_admin"],
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

        yield

        self.run_variables_deduplicate.delete()
        self.run_deduplicate.delete()

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
