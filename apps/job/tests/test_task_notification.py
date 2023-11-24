from unittest.mock import MagicMock, Mock, patch

from job.tasks.notification import (
    send_missed_schedule_notification,
    send_run_notification,
)


@patch("job.tasks.notification.logger")
def test_send_run_notification(mock_logger, test_runs):
    send_run_notification(test_runs["run_1"].uuid)
    mock_logger.warning.assert_not_called()
    mock_logger.info.assert_called_once_with(
        f"Received message to send notifications for run {test_runs['run_1'].suuid}."
    )


@patch("job.tasks.notification.logger")
def test_send_run_notification_no_notifications(mock_logger, test_runs):
    send_run_notification(test_runs["run_3"].uuid)
    mock_logger.info.assert_called_with(f"No notifications configured for run {test_runs['run_3'].suuid}.")


@patch("job.tasks.notification.logger")
@patch("run.models.run.Run.objects.get")
def test_send_run_notification_no_config(mock_get_run, mock_logger):
    mock_run = Mock()
    mock_run.suuid = "test_suuid"
    mock_run.status = "test_status"
    mock_run.jobdef.name = "test_job"
    mock_run.package = None

    mock_get_run.return_value = mock_run

    send_run_notification("test_suuid")
    mock_logger.warning.assert_called_once_with("Cannot send notifcations. No job config found for run test_suuid.")


@patch("job.tasks.notification.logger")
def test_send_missed_schedule_notification(mock_logger, test_jobs, test_storage_files):
    send_missed_schedule_notification(test_jobs["my-test-job"].uuid)
    mock_logger.warning.assert_not_called()
    mock_logger.info.assert_called_once_with(
        f"Received message to send notifications for missed schedule for job {test_jobs['my-test-job'].suuid}."
    )


@patch("job.tasks.notification.logger")
def test_send_missed_schedule_notification_no_notifications(mock_logger, test_jobs, test_storage_files):
    send_missed_schedule_notification(test_jobs["job_private"].uuid)
    mock_logger.info.assert_called_with(f"No notifications configured for job {test_jobs['job_private'].suuid}.")


@patch("job.tasks.notification.logger")
def test_send_missed_schedule_notification_no_package(mock_logger, test_jobs):
    with patch(
        "package.models.Package.objects.active",
        return_value=Mock(
            filter=Mock(return_value=Mock(order_by=Mock(return_value=Mock(first=Mock(return_value=None)))))
        ),
    ):
        send_missed_schedule_notification(test_jobs["job_private"].uuid)

    mock_logger.warning.assert_called_with(
        f"Cannot send notifcations. No package found for job {test_jobs['job_private'].suuid}."
    )


@patch("job.tasks.notification.logger")
@patch("job.models.JobDef.objects.get")
def test_send_missed_schedule_notification_no_config(mock_get_job, mock_logger):
    mock_job = Mock()
    mock_job.suuid = "test_suuid"
    mock_job.name = "test_job"

    mock_package = MagicMock()
    mock_package.get_askanna_config.return_value = None

    mock_get_job.return_value = mock_job

    with patch(
        "package.models.Package.objects.active",
        return_value=Mock(
            filter=Mock(return_value=Mock(order_by=Mock(return_value=Mock(first=Mock(return_value=mock_package)))))
        ),
    ), patch.object(mock_package, "get_askanna_config", return_value=None):
        send_missed_schedule_notification("test_suuid")

    mock_logger.warning.assert_called_once_with("Cannot send notifcations. No config found for job test_suuid.")
