from unittest.mock import patch

import pytest
from django.test import TestCase

from job.models import RunImage
from run.models import Run


def test_run_function__str__run_with_name(test_runs):
    assert str(test_runs["run_1"]) == f"Run: test run 1 ({test_runs['run_1'].suuid})"


def test_run_function__str__run_with_no_name(test_runs):
    assert str(test_runs["run_2"]) == f"Run: {test_runs['run_2'].suuid}"


def test_run_function_set_status(test_runs):
    assert test_runs["run_3"].status == "FAILED"
    modified_at_before = test_runs["run_3"].modified_at

    test_runs["run_3"].set_status("COMPLETED")
    assert test_runs["run_3"].status == "COMPLETED"
    assert test_runs["run_3"].modified_at > modified_at_before


def test_run_function_set_run_image(test_runs):
    run: Run = test_runs["run_1"]
    run_modified_at_before = run.modified_at

    run_image_1 = RunImage.objects.create(name="tes_1", digest="test_1")

    assert run.run_image is None

    run.set_run_image(run_image_1)
    assert run.run_image == run_image_1
    assert run.modified_at != run_modified_at_before

    test_1_modified_at_before = test_runs["run_1"].modified_at

    run.set_run_image(run_image_1)
    assert run.run_image == run_image_1
    assert run.modified_at != run_modified_at_before
    assert run.modified_at != test_1_modified_at_before

    run_image_2 = RunImage.objects.create(name="test_2", digest="test_2")

    run.set_run_image(run_image_2)
    assert run.run_image == run_image_2

    run_image_1.delete()
    run_image_2.delete()


def test_run_function_set_timezone(test_runs):
    run: Run = test_runs["run_1"]
    run_modified_at_before = run.modified_at

    assert run.timezone is not None

    run.set_timezone("Europe/Amsterdam")
    assert run.timezone == "Europe/Amsterdam"
    assert run.modified_at != run_modified_at_before

    test_1_modified_at_before = test_runs["run_1"].modified_at

    run.set_timezone("Europe/Amsterdam")
    assert run.timezone == "Europe/Amsterdam"
    assert run.modified_at != run_modified_at_before
    assert run.modified_at != test_1_modified_at_before

    run.set_timezone("Europe/Brussels")
    assert run.timezone == "Europe/Brussels"


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


class TestRunAddToLogQueue(TestCase):
    @pytest.fixture(autouse=True)
    def setup(self, test_runs):
        self.test_run: Run = test_runs["run_4"]

    @patch("config.celery_app.app.send_task")
    def test_run_function_add_to_log(self, mock_celery_app):
        assert hasattr(self.test_run, "log_queue_last_save") is False
        self.test_run.add_to_log("test log")

        assert len(self.test_run.get_log()) == 1
        assert self.test_run.get_log()[0][2] == "test log"
        assert hasattr(self.test_run, "log_queue_last_save") is True

        mock_celery_app.assert_called_once_with(
            "run.tasks.save_run_log",
            kwargs={"run_suuid": self.test_run.suuid},
        )

    @patch("config.celery_app.app.send_task")
    def test_run_function_add_to_log_timeout_save_run_log(self, mock_celery_app):
        assert hasattr(self.test_run, "log_queue_last_save") is False

        self.test_run.add_to_log("test log")
        self.test_run.add_to_log("test log 2")

        assert len(self.test_run.get_log()) == 2
        assert self.test_run.get_log()[0][2] == "test log"
        assert self.test_run.get_log()[1][2] == "test log 2"
        assert hasattr(self.test_run, "log_queue_last_save") is True

        mock_celery_app.assert_called_once_with(
            "run.tasks.save_run_log",
            kwargs={"run_suuid": self.test_run.suuid},
        )
