import json
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest
from django.core import mail

from core.utils import parse_string
from job.mailer import (
    fill_in_mail_variable,
    get_job_notification_receivers,
    get_notification_variables,
    send_notification,
)
from job.models import JobDef
from run.models import Run
from storage.models import File
from variable.models import Variable

pytestmark = pytest.mark.django_db


def test_string_parsing():
    string = "${to} be ${or} ${to} be"
    variables = {
        "to": "be",
        "or": "not",
    }
    assert parse_string(string, variables) == "be be not be be"


def test_mail_variable_deduplicated():
    string = "${project_variable_mail_notifications}"
    variables = {
        "project_variable_mail_notifications": "anna@askanna.io,robot@askanna.io",
    }
    assert fill_in_mail_variable(string, variables) == ["anna@askanna.io", "robot@askanna.io"]


def test_get_notification_receivers(test_jobs, test_memberships):
    variables = {
        "project_variable_mail_notifications": "anna@askanna.io,robot@askanna.io",
    }
    receivers = get_job_notification_receivers(
        ["${project_variable_mail_notifications}"], variables, test_jobs["job_private"]
    )
    assert set(receivers) == {
        "anna@askanna.io",
        "robot@askanna.io",
    }
    assert "workspace admins" not in receivers
    assert "workspace members" not in receivers

    receivers = get_job_notification_receivers(
        ["${project_variable_mail_notifications}", "workspace admins"], variables, test_jobs["job_private"]
    )
    assert set(receivers) == {
        "anna@askanna.io",
        "robot@askanna.io",
        test_memberships["workspace_private_admin"].user.email,
    }
    assert "workspace admins" not in receivers
    assert "workspace members" not in receivers

    receivers = get_job_notification_receivers(
        ["${project_variable_mail_notifications}", "workspace admins", "workspace members"],
        variables,
        test_jobs["job_private"],
    )
    assert set(receivers) == {
        "anna@askanna.io",
        "robot@askanna.io",
        test_memberships["workspace_private_admin"].user.email,
        test_memberships["workspace_private_member"].user.email,
        test_memberships["workspace_private_viewer"].user.email,
    }
    assert "workspace admins" not in receivers
    assert "workspace members" not in receivers


def test_send_notification_mail_running(test_runs):
    run = test_runs["run_1"]
    package = run.package
    config_yml = package.get_askanna_config()
    job_config = config_yml.jobs.get(run.jobdef.name)

    send_notification("IN_PROGRESS", run=run, job_config=job_config)

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == 'Running "test run 1" | test project private'
    assert len(mail.outbox[0].to) == 1
    assert mail.outbox[0].to[0] == "anna@askanna.io"


def test_get_notification_variables_for_job():
    job = Mock(spec=JobDef)
    job.project = Mock()

    variable = Mock(spec=Variable)
    variable.name = "var_name"
    variable.value = "var_value"

    mock_queryset = MagicMock()
    mock_queryset.__iter__.return_value = iter([variable])

    with patch("variable.models.Variable.objects.filter", return_value=mock_queryset):
        job_variables = get_notification_variables(job)
    assert job_variables == {"var_name": "var_value"}


def test_get_notification_variables_for_run():
    # Create a mock job and project
    job = Mock(spec=JobDef)
    job.project = Mock()

    # Create a mock run with a payload
    run: Run = Mock(spec=Run)
    run.payload_file = Mock(spec=File)
    run.payload_file.file.open = mock_open(
        read_data=json.dumps(
            {
                "key": "value",
                "key_2": ["value_1", "value_2"],
                "key_3": 123,
            }
        )
    )

    variable = Mock(spec=Variable)
    variable.name = "var_name"
    variable.value = "var_value"

    # Mock Variable.objects.filter to return a queryset with one variable
    mock_queryset = MagicMock()
    mock_queryset.__iter__.return_value = iter([variable])

    with patch("variable.models.Variable.objects.filter", return_value=mock_queryset):
        run_variables = get_notification_variables(job, run)
    assert run_variables == {
        "key": "value",
        "key_2": json.dumps(["value_1", "value_2"]),
        "key_3": 123,
        "var_name": "var_value",
    }
