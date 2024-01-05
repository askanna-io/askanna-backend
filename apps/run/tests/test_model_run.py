from unittest.mock import patch

import pytest
from django.test import TestCase


def test_run_function__str__run_with_name(test_runs):
    assert str(test_runs["run_1"]) == f"test run 1 ({test_runs['run_1'].suuid})"


def test_run_function__str__run_with_no_name(test_runs):
    assert str(test_runs["run_2"]) == str(test_runs["run_2"].suuid)


def test_run_function_set_status(test_runs):
    assert test_runs["run_3"].status == "FAILED"
    modified_at_before = test_runs["run_3"].modified_at

    test_runs["run_3"].set_status("COMPLETED")
    assert test_runs["run_3"].status == "COMPLETED"
    assert test_runs["run_3"].modified_at > modified_at_before


def test_run_function_set_finished_at(test_runs):
    assert test_runs["run_4"].started_at is not None
    assert test_runs["run_4"].finished_at is None
    assert test_runs["run_4"].duration is None

    modified_at_before = test_runs["run_2"].modified_at
    test_runs["run_4"].set_finished_at()

    assert test_runs["run_4"].modified_at > modified_at_before
    assert test_runs["run_4"].started_at is not None
    assert test_runs["run_4"].finished_at is not None
    assert test_runs["run_4"].finished_at > test_runs["run_4"].started_at

    duration = (test_runs["run_4"].finished_at - test_runs["run_4"].started_at).seconds

    assert test_runs["run_4"].duration == duration


class TestRunToStatusFunctions(TestCase):
    @pytest.fixture(autouse=True)
    def setup(self, test_runs):
        self.test_run = test_runs["run_4"]
        self.test_run.started_at = None

    @patch("config.celery_app.app.send_task")
    def test_run_function_to_pending(self, mock_celery_app):
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is None

        modified_at_before = self.test_run.modified_at
        with self.captureOnCommitCallbacks(execute=True) as callbacks:
            self.test_run.to_pending()

        assert self.test_run.status == "PENDING"
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is None
        assert self.test_run.modified_at > modified_at_before

        assert len(callbacks) == 1

        mock_celery_app.assert_called_once_with(
            "job.tasks.send_run_notification",
            kwargs={"run_suuid": self.test_run.suuid},
        )

    def test_run_function_to_inprogress(self):
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is None

        modified_at_before = self.test_run.modified_at
        self.test_run.to_inprogress()

        assert self.test_run.status == "IN_PROGRESS"
        assert self.test_run.started_at is not None
        assert self.test_run.finished_at is None
        assert self.test_run.modified_at > modified_at_before

    def test_run_function_to_completed(self):
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is None

        modified_at_before = self.test_run.modified_at
        self.test_run.to_completed()

        assert self.test_run.status == "COMPLETED"
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is not None
        assert self.test_run.modified_at > modified_at_before

    def test_run_function_to_failed(self):
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is None

        modified_at_before = self.test_run.modified_at
        self.test_run.to_failed()

        assert self.test_run.status == "FAILED"
        assert self.test_run.started_at is None
        assert self.test_run.finished_at is not None
        assert self.test_run.modified_at > modified_at_before
