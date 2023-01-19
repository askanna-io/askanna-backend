import unittest

import pytest
from core.utils import parse_string
from job.mailer import fill_in_mail_variable, send_run_notification
from job.tests.base import BaseJobTestDef
from rest_framework.test import APITestCase

pytestmark = pytest.mark.django_db


class TestJobMailerUtils(unittest.TestCase):
    def test_string_parsing(self):
        string = "${to} be ${or} ${to} be"
        variables = {
            "to": "be",
            "or": "not",
        }
        self.assertEqual(parse_string(string, variables), "be be not be be")

    def test_mail_variable_deduplicated(self):
        string = "${project_variable_mail_notifications}"
        variables = {
            "project_variable_mail_notifications": "anna@askanna.io,robot@askanna.io",
        }
        self.assertEqual(
            fill_in_mail_variable(string, variables),
            [
                "anna@askanna.io",
                "robot@askanna.io",
            ],
        )


class TestSendNotification(BaseJobTestDef, APITestCase):
    def test_send_notification_mail_running(self):
        run = self.runs["run4"]
        package = run.package
        config_yml = package.get_askanna_config()
        job_config = config_yml.jobs.get(run.jobdef.name)
        send_run_notification("IN_PROGRESS", run=run, job_config=job_config)
