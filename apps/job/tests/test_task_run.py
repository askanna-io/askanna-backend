from unittest.mock import Mock, patch

from job.tasks.run import (
    create_run_variable_object,
    get_job_config,
    get_run_variables,
    get_variable_type,
    start_run,
)
from run.models import RunVariable


def test_create_run_variable_object(test_runs):
    run = test_runs["run_1"]

    run_variable = create_run_variable_object(
        run=run,
        variable_name="foo",
        variable_value="bar",
        variable_type="string",
    )

    assert isinstance(run_variable, RunVariable)
    assert run_variable.run == run
    assert run_variable.variable.get("name") == "foo"
    assert run_variable.variable.get("value") == "bar"
    assert run_variable.variable.get("type") == "string"
    assert run_variable.label == []

    run_variable = create_run_variable_object(
        run=run,
        variable_name="bar",
        variable_value=True,
        variable_type="boolean",
        variable_labels=[{"name": "source", "value": "worker", "type": "string"}],
    )

    assert isinstance(run_variable, RunVariable)
    assert run_variable.run == run
    assert run_variable.variable.get("name") == "bar"
    assert run_variable.variable.get("value") is True
    assert run_variable.variable.get("type") == "boolean"
    assert run_variable.label == [{"name": "source", "value": "worker", "type": "string"}]


def test_get_run_variables(test_runs):
    run = test_runs["run_1"]
    job_config = get_job_config(run=run)

    assert run.variables.count() == 0

    run.project.variables.create(name="foo", value="bar")
    run.project.variables.create(name="bar", value="foo", is_masked=True)

    run_variables = get_run_variables(run=run, job_config=job_config)

    assert len(run_variables) == 10
    # Three vraialbes are set for run environment, but are not tracked as a run variable
    assert run.variables.count() == 7

    # Run 2 has a payload with variables
    run = test_runs["run_2"]
    run.variables.all().delete()
    job_config = get_job_config(run=run)

    assert run.variables.count() == 0
    run_variables = get_run_variables(run=run, job_config=job_config)

    assert len(run_variables) == 12
    # Three variables are set for run environment, but are not tracked as a run variable
    assert run.variables.count() == 9


def test_get_variable_type():
    assert get_variable_type("foo") == "string"
    assert get_variable_type(1) == "integer"
    assert get_variable_type(1.0) == "float"
    assert get_variable_type(True) == "boolean"
    assert get_variable_type({"foo": "bar"}) == "dictionary"
    assert get_variable_type(["foo", "bar"]) == "list"
    assert get_variable_type(None) == "null"
    assert get_variable_type(object) == "unknown"


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

    assert mock_run.output.log.call_count == 3
    assert mock_run.output.log.call_args_list[0][0][0] == "Could not find code package"

    assert mock_run.to_failed.call_count == 1
