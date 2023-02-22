from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from run.models import Run, RunMetric, RunMetricMeta
from run.tasks.metric import post_run_deduplicate_metrics

from .base import BaseRunTest, metric_response_good, metric_response_good_small


class TestRunMetricModel(BaseRunTest, APITestCase):
    """
    Test RunMetric model functions
    """

    def test_runmetrics_function_load_from_file(self):
        assert self.runmetrics["run1"].load_from_file() == metric_response_good

    def test_runmetrics_function_update_meta_no_metrics_and_no_labels(self):
        modified_at_before = self.runmetrics["run7"].modified_at
        self.runmetrics["run7"].update_meta()
        assert self.runmetrics["run7"].modified_at == modified_at_before
        assert self.runmetrics["run7"].count == 0
        assert self.runmetrics["run7"].size == 0
        assert self.runmetrics["run7"].metric_names is None
        assert self.runmetrics["run7"].label_names is None

    def test_runmetrics_function_update_meta(self):
        modified_at_before_1 = self.runmetrics["run7"].modified_at
        self.runmetrics["run7"].update_meta()
        assert self.runmetrics["run7"].modified_at == modified_at_before_1
        assert self.runmetrics["run7"].count == 0
        assert self.runmetrics["run7"].size == 0
        assert self.runmetrics["run7"].metric_names is None
        assert self.runmetrics["run7"].label_names is None

        self.runmetrics["run7"].metrics = metric_response_good
        self.runmetrics["run7"].save()

        modified_at_before_2 = self.runmetrics["run7"].modified_at
        self.runmetrics["run7"].update_meta()
        assert self.runmetrics["run7"].modified_at > modified_at_before_2
        assert self.runmetrics["run7"].count == 4
        assert self.runmetrics["run7"].size == 1202

        expected_metric_names = [
            {"name": "Accuracy", "type": "integer", "count": 2},
            {"name": "Quality", "type": "string", "count": 2},
        ]
        assert len(self.runmetrics["run7"].metric_names) == 2  # type: ignore
        assert self.runmetrics["run7"].metric_names[0] in expected_metric_names  # type: ignore
        assert self.runmetrics["run7"].metric_names[1] in expected_metric_names  # type: ignore

        expected_label_names = [
            {"name": "city", "type": "string"},
            {"name": "product", "type": "string"},
            {"name": "Missing data", "type": "boolean"},
        ]
        assert len(self.runmetrics["run7"].label_names) == 3  # type: ignore
        assert self.runmetrics["run7"].label_names[0] in expected_label_names  # type: ignore
        assert self.runmetrics["run7"].label_names[1] in expected_label_names  # type: ignore
        assert self.runmetrics["run7"].label_names[2] in expected_label_names  # type: ignore

    def test_runmetrics_function_update_meta_no_labels(self):
        self.runmetrics["run6"].update_meta()
        assert self.runmetrics["run6"].count == 2
        assert self.runmetrics["run6"].size == 340
        assert self.runmetrics["run6"].metric_names is not None
        assert self.runmetrics["run6"].label_names is None


class TestMetricListAPI(BaseRunTest, APITestCase):
    """
    Test to list the RunMetric
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runmetrics["run1"].suuid,
            },
        )

    def test_list_as_askanna_admin(self):
        """
        We can list metrics as an AskAnna admin,
        but response will be empty because of not having access to this workspace.
        """
        self.activate_user("anna")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_admin(self):
        """
        We can list metrics as admin of a workspace
        """
        self.activate_user("admin")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_as_member(self):
        """
        We can list metrics as member of a workspace
        """
        self.activate_user("member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

    def test_list_as_non_member(self):
        """
        We can list metrics as non_member of a workspace,
        but response will be empty because of not having access to this workspace.
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_anonymous(self):
        """
        Anonymous user can list metrics, but only public ones
        So we expect here an empty list as result
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0  # type: ignore

    def test_list_as_member_order_by_metric_name(self):
        """
        We get detail metrics as member of a workspace and order them by metric name
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            {
                "order_by": "metric.name",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 4  # type: ignore

        response_reversed = self.client.get(
            self.url,
            {
                "order_by": "-metric.name",
            },
        )
        assert response_reversed.status_code == status.HTTP_200_OK
        assert len(response_reversed.data["results"]) == 4  # type: ignore

        assert (
            response.data["results"][0]["metric"]["name"]  # type: ignore
            == response_reversed.data["results"][3]["metric"]["name"]  # type: ignore
        )

    def test_list_as_member_filter_metric_name(self):
        """
        We test the filter by metric name
        """
        self.activate_user("member")
        response = self.client.get(
            self.url,
            {"metric_name": "Accuracy"},
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_member_filter_label_name(self):
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


class TestMetricPublicProjectListAPI(BaseRunTest, APITestCase):
    """
    Test to list the M<etrics from a job in a public project
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-list",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runmetrics["run6"].suuid,
            },
        )

    def test_list_as_non_member(self):
        """
        Public project run metrics are listable by anyone
        """
        self.activate_user("non_member")
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore

    def test_list_as_anonymous(self):
        """
        Public project run metrics are listable by anyone
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2  # type: ignore


class TestMetricUpdateAPI(BaseRunTest, APITestCase):
    """
    We update the metrics of a run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "run-metric-detail",
            kwargs={
                "version": "v1",
                "parent_lookup_run__suuid": self.runmetrics.get("run1").suuid,
                "run__suuid": self.runmetrics.get("run1").suuid,
            },
        )

    def test_update_as_askanna_admin(self):
        """
        We cannot update metrics as an AskAnna admin who is not member of a workspace
        """
        self.activate_user("anna")
        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_as_admin(self):
        """
        We update metrics as admin of a workspace
        """
        self.activate_user("admin")
        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None  # type: ignore

    def test_update_as_member(self):
        """
        We update metrics as member of a workspace
        """
        self.activate_user("member")
        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data is None  # type: ignore

    def test_update_as_non_member(self):
        """
        We cannot update metrics as non-member of a workspace
        """
        self.activate_user("non_member")
        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_as_anonymous(self):
        """
        We cannot update metrics as anonymous
        """
        response = self.client.put(
            self.url,
            {"metrics": metric_response_good_small},
            format="json",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestRunMetricDeduplicate(BaseRunTest, APITestCase):
    def setUp(self):
        super().setUp()
        self.run_deduplicate = Run.objects.create(
            name="deduplicate",
            description="test deduplicate",
            package=self.package,
            jobdef=self.jobdef,
            status="COMPLETED",
            created_by=self.users.get("member"),
            member=self.members.get("member"),
            run_image=self.run_image,
            duration=123,
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

    def tearDown(self):
        super().tearDown()
        self.run_deduplicate.delete()
