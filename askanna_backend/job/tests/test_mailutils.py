# -*- coding: utf-8 -*-
import unittest

import pytest
from rest_framework.test import APITestCase

from job.mailer import parsestring, fill_in_mail_variable, send_run_notification
from job.tests.base import BaseJobTestDef

pytestmark = pytest.mark.django_db


class TestJobMailerUtils(unittest.TestCase):
    def test_string_parsing(self):
        string = "${to} be ${or} ${to} be"
        variables = {
            "to": "be",
            "or": "not",
        }
        self.assertEqual(parsestring(string, variables), "be be not be be")

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
        run = self.jobruns.get("run4")

        package = run.package
        configyml = package.get_askanna_config()
        print(configyml)
        job_config = configyml.jobs.get(run.jobdef.name)
        print(job_config)
        send_run_notification("IN_PROGRESS", run, job_config)