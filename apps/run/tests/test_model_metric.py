import pytest

from run.models import Run, RunMetric, RunMetricMeta
from run.tasks.metric import post_run_deduplicate_metrics


class TestRunMetricModel:
    """
    Test RunMetric model functions
    """

    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_run_metrics, metric_response_good):
        self.run_metrics = test_run_metrics
        self.metric_response_good = metric_response_good

    def test_runmetrics_function_load_from_file(self):
        assert self.run_metrics["run_2"].load_from_file() == self.metric_response_good

    def test_runmetrics_function_update_meta_no_metrics_and_no_labels(self):
        modified_at_before = self.run_metrics["run_3"].modified_at
        self.run_metrics["run_3"].update_meta()
        assert self.run_metrics["run_3"].modified_at == modified_at_before
        assert self.run_metrics["run_3"].count == 0
        assert self.run_metrics["run_3"].size == 0
        assert self.run_metrics["run_3"].metric_names is None
        assert self.run_metrics["run_3"].label_names is None

    def test_runmetrics_function_update_meta(self):
        modified_at_before_1 = self.run_metrics["run_3"].modified_at
        self.run_metrics["run_3"].update_meta()
        assert self.run_metrics["run_3"].modified_at == modified_at_before_1
        assert self.run_metrics["run_3"].count == 0
        assert self.run_metrics["run_3"].size == 0
        assert self.run_metrics["run_3"].metric_names is None
        assert self.run_metrics["run_3"].label_names is None

        self.run_metrics["run_3"].metrics = self.metric_response_good
        self.run_metrics["run_3"].save()

        modified_at_before_2 = self.run_metrics["run_3"].modified_at
        self.run_metrics["run_3"].update_meta()
        assert self.run_metrics["run_3"].modified_at > modified_at_before_2
        assert self.run_metrics["run_3"].count == 4
        assert self.run_metrics["run_3"].size == 1202

        expected_metric_names = [
            {"name": "Accuracy", "type": "integer", "count": 2},
            {"name": "Quality", "type": "string", "count": 2},
        ]
        assert len(self.run_metrics["run_3"].metric_names) == 2
        assert self.run_metrics["run_3"].metric_names[0] in expected_metric_names
        assert self.run_metrics["run_3"].metric_names[1] in expected_metric_names

        expected_label_names = [
            {"name": "city", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ]
        assert len(self.run_metrics["run_3"].label_names) == 3
        assert self.run_metrics["run_3"].label_names[0] in expected_label_names
        assert self.run_metrics["run_3"].label_names[1] in expected_label_names
        assert self.run_metrics["run_3"].label_names[2] in expected_label_names

    def test_runmetrics_function_update_meta_no_labels(self):
        self.run_metrics["run_5"].update_meta()
        assert self.run_metrics["run_5"].count == 2
        assert self.run_metrics["run_5"].size == 340
        assert self.run_metrics["run_5"].metric_names is not None
        assert self.run_metrics["run_5"].label_names is None


class TestRunMetricDeduplicate:
    """
    Test RunMetric model functions to deduplicate metrics
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

        self.metric_to_test_deduplicate = [
            {
                "run_suuid": self.run_deduplicate.suuid,
                "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": self.run_deduplicate.suuid,
                "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

        self.run_metrics_deduplicate = RunMetricMeta.objects.create(
            run=self.run_deduplicate, metrics=self.metric_to_test_deduplicate
        )

        yield

        self.run_metrics_deduplicate.delete()
        self.run_deduplicate.delete()

    def test_run_metrics_deduplicate(self):
        #  Count metrics before adding duplicates
        metrics = RunMetric.objects.filter(run_suuid=self.run_deduplicate.suuid)
        assert len(metrics) == 2

        metric_record = RunMetricMeta.objects.get(uuid=self.run_metrics_deduplicate.uuid)
        assert metric_record.count == 2

        # Add duplicate metrics
        for metric in self.metric_to_test_deduplicate:
            RunMetric.objects.create(
                project_suuid=self.run_deduplicate.jobdef.project.suuid,
                job_suuid=self.run_deduplicate.jobdef.suuid,
                run_suuid=self.run_deduplicate.suuid,
                run=self.run_deduplicate,
                metric=metric["metric"],
                label=metric["label"],
                created_at=metric["created_at"],
            )
        self.run_metrics_deduplicate.update_meta()

        metrics_with_duplicates = RunMetric.objects.filter(run_suuid=self.run_deduplicate.suuid)
        assert len(metrics_with_duplicates) == 4
        metric_record_with_duplicates = RunMetricMeta.objects.get(uuid=self.run_metrics_deduplicate.uuid)
        assert metric_record_with_duplicates.count == 4

        # Dedepulicate run metric records
        post_run_deduplicate_metrics(run_uuid=self.run_deduplicate.uuid)

        metrics_after_deduplicates = RunMetric.objects.filter(run_suuid=self.run_deduplicate.suuid)
        assert len(metrics_after_deduplicates) == 2
        metric_record_after_deduplicate = RunMetricMeta.objects.get(uuid=self.run_metrics_deduplicate.uuid)
        assert metric_record_after_deduplicate.count == 2
