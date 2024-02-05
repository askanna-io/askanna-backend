from unittest.mock import Mock, patch

from job.tasks.run import start_run


@patch("job.tasks.run.logger")
@patch("run.models.run.Run.objects.get")
def test_start_run_no_package(mock_get_run, mock_logger, db):
    mock_run = Mock()
    mock_run.suuid = "test_suuid"
    mock_run.jobdef.name = "test_job"
    mock_run.package = None

    mock_get_run.return_value = mock_run

    start_run("test_suuid")

    mock_logger.info.assert_called_once_with("Received message to start run test_suuid.")

    assert mock_run.add_to_log.call_count == 3
    assert mock_run.add_to_log.call_args_list[0][0][0] == "Could not find code package"

    assert mock_run.to_failed.call_count == 1
