import json
import unittest
from unittest.mock import Mock, patch

import pytest
from django.core.files.base import ContentFile
from django.utils import timezone

from core.container import RegistryAuthenticationError, RegistryContainerPullError
from job.utils import (
    create_run_variable_object,
    get_job_config,
    get_run_image,
    get_run_variables,
    get_variable_type,
)
from run.models import RunVariable
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file


class TestGetJobConfig(unittest.TestCase):
    def setUp(self):
        self.run = Mock()
        self.run.package = Mock()
        self.run.job = Mock()
        self.run.job.name = "test_job"
        self.run.package.get_askanna_config = Mock()

    def test_get_job_config_no_package(self):
        self.run.package = None
        result = get_job_config(self.run)

        self.run.add_to_log.assert_called_with("Could not find code package")
        assert result is None

    def test_get_job_config_no_askanna_config(self):
        self.run.package.get_askanna_config.return_value = None

        result = get_job_config(self.run)

        self.run.add_to_log.assert_called_with("Could not find askanna.yml")
        assert result is None

    def test_get_job_config_no_job_config(self):
        askanna_config = Mock()
        askanna_config.jobs = {}
        self.run.package.get_askanna_config.return_value = askanna_config

        result = get_job_config(self.run)

        self.run.add_to_log.assert_called_with(
            "When you updated the askanna.yml, check if you pushed the latest code to AskAnna."
        )
        assert result is None

    def test_get_job_config_success(self):
        job_config = Mock()
        askanna_config = Mock()
        askanna_config.jobs = {self.run.job.name: job_config}
        self.run.package.get_askanna_config.return_value = askanna_config

        result = get_job_config(self.run)

        assert result == job_config


class TestGetVariableType:
    def test_get_variable_type(self):
        assert get_variable_type("foo") == "string"
        assert get_variable_type(1) == "integer"
        assert get_variable_type(1.0) == "float"
        assert get_variable_type(True) == "boolean"
        assert get_variable_type({"foo": "bar"}) == "dictionary"
        assert get_variable_type(["foo", "bar"]) == "list"
        assert get_variable_type(None) == "null"
        assert get_variable_type(object) == "unknown"


class TestCreateRunVariableObject:
    @pytest.fixture(autouse=True)
    def _set_fixtures(
        self,
        test_runs,
    ):
        self.run = test_runs["run_1"]

    def test_create_run_variable_object(self):
        run_variable = create_run_variable_object(
            run=self.run,
            variable_name="foo",
            variable_value="bar",
            variable_type="string",
        )

        assert isinstance(run_variable, RunVariable)
        assert run_variable.run == self.run
        assert run_variable.variable.get("name") == "foo"
        assert run_variable.variable.get("value") == "bar"
        assert run_variable.variable.get("type") == "string"
        assert run_variable.label == []

    def test_create_run_variable_object_with_labels(self):
        run_variable = create_run_variable_object(
            run=self.run,
            variable_name="bar",
            variable_value=True,
            variable_type="boolean",
            variable_labels=[{"name": "source", "value": "worker", "type": "string"}],
        )

        assert isinstance(run_variable, RunVariable)
        assert run_variable.run == self.run
        assert run_variable.variable.get("name") == "bar"
        assert run_variable.variable.get("value") is True
        assert run_variable.variable.get("type") == "boolean"
        assert run_variable.label == [{"name": "source", "value": "worker", "type": "string"}]


class TestGetRunVariables:
    @pytest.fixture(autouse=True)
    def _set_fixtures(
        self,
        test_runs,
    ):
        self.run_1 = test_runs["run_1"]
        self.run_2 = test_runs["run_2"]

    def test_get_run_variables(self):
        job_config = get_job_config(run=self.run_1)

        assert self.run_1.variables.count() == 0

        run_variables = get_run_variables(run=self.run_1, job_config=job_config)

        assert len(run_variables) == 8
        # Three variables are set for run environment, but are not tracked as a run variable
        assert self.run_1.variables.count() == 5

    def test_get_run_variables_with_project_variables(self):
        job_config = get_job_config(run=self.run_1)

        assert self.run_1.variables.count() == 0

        self.run_1.project.variables.create(name="foo", value="bar")
        self.run_1.project.variables.create(name="bar", value="foo", is_masked=True)

        run_variables = get_run_variables(run=self.run_1, job_config=job_config)

        assert len(run_variables) == 10
        # Three variables are set for run environment, but are not tracked as a run variable
        assert self.run_1.variables.count() == 7

    def test_get_run_variables_with_payload(self):
        # Run 2 has a payload with variables
        job_config = get_job_config(run=self.run_2)

        self.run_2.variables.all().delete()
        assert self.run_2.variables.count() == 0

        run_variables = get_run_variables(run=self.run_2, job_config=job_config)

        assert len(run_variables) == 10
        # Three variables are set for run environment, but are not tracked as a run variable
        assert self.run_2.variables.count() == 7
        assert "AA_PAYLOAD_PATH" in run_variables

    def test_get_run_variables_with_payload_different_types(self):
        # Run 2 has a payload with variables
        job_config = get_job_config(run=self.run_2)

        self.run_2.variables.all().delete()
        assert self.run_2.variables.count() == 0

        self.run_2.payload_file.delete()
        payload_json = {
            "foo": "bar",
            "bar": "foo",
            "baz": 1,
            "qux": 1.0,
            "quux": True,
            "quuz": None,
            "corge": ["foo", "bar"],
        }
        payload_content_file = ContentFile(
            json.dumps(payload_json).encode(),
            name="payload.json",
        )
        self.run_2.payload_file = File.objects.create(
            name=payload_content_file.name,
            file=payload_content_file,
            size=payload_content_file.size,
            etag=get_md5_from_file(payload_content_file),
            content_type=get_content_type_from_file(payload_content_file),
            completed_at=timezone.now(),
            created_for=self.run_2,
            created_by=self.run_2.created_by_member,
        )
        self.run_2.save()

        run_variables = get_run_variables(run=self.run_2, job_config=job_config)

        assert len(run_variables) == 16
        # Three variables are set for run environment, but are not tracked as a run variable
        assert self.run_2.variables.count() == 13
        assert "AA_PAYLOAD_PATH" in run_variables

    def test_get_run_variables_with_payload_truncate_long_values(self):
        # If value longer then 10,000 characters, it should be truncated
        job_config = get_job_config(run=self.run_2)

        self.run_2.variables.all().delete()
        assert self.run_2.variables.count() == 0

        self.run_2.payload_file.delete()
        payload_json = {
            "foo": "bar",
            "bar": "a" * 11000,
            "woz": [i for i in range(11000)],
        }
        payload_content_file = ContentFile(
            json.dumps(payload_json).encode(),
            name="payload.json",
        )
        self.run_2.payload_file = File.objects.create(
            name=payload_content_file.name,
            file=payload_content_file,
            size=payload_content_file.size,
            etag=get_md5_from_file(payload_content_file),
            content_type=get_content_type_from_file(payload_content_file),
            completed_at=timezone.now(),
            created_for=self.run_2,
            created_by=self.run_2.created_by_member,
        )
        self.run_2.save()

        run_variables = get_run_variables(run=self.run_2, job_config=job_config)

        assert len(run_variables) == 12
        # Three variables are set for run environment, but are not tracked as a run variable
        assert self.run_2.variables.count() == 9
        assert "AA_PAYLOAD_PATH" in run_variables

        assert len(run_variables["bar"]) == 10000
        assert len(run_variables["bar"]) != len(payload_json["bar"])
        assert len(run_variables["woz"]) == 10000
        assert len(run_variables["woz"]) != len(payload_json["woz"])


class TestGetRunImage(unittest.TestCase):
    def setUp(self):
        self.run = Mock()
        self.run.to_failed.return_value = None

        self.job_config = Mock()
        self.job_config.environment.image = "test_image"
        self.job_config.environment.credentials.username = None
        self.job_config.environment.credentials.password = None

        self.run_variables = {}

        self.docker_client = Mock()

    @patch("core.container.RegistryImageHelper.get_image_info")
    @patch("core.container.ContainerImageBuilder.get_image")
    def test_get_run_image_success(self, mock_get_image, mock_get_image_info):
        mock_get_image_info.return_value = Mock()
        mock_get_image.return_value = Mock()

        result = get_run_image(self.run, self.job_config, self.run_variables, self.docker_client)

        assert result is not None
        assert self.run.add_to_log.call_count == 3
        assert "Run failed" not in self.run.add_to_log.call_args_list[-1][0][0]
        assert self.run.to_failed.call_count == 0

    @patch("core.container.RegistryImageHelper.get_image_info")
    def test_get_run_image_info_auth_error(self, mock_get_image_info):
        mock_get_image_info.side_effect = RegistryAuthenticationError

        result = get_run_image(self.run, self.job_config, self.run_variables, self.docker_client)

        assert result is None
        assert self.run.to_failed.call_count == 0

    @patch("core.container.RegistryImageHelper.get_image_info")
    def test_get_run_image_info_exception(self, mock_get_image_info):
        mock_get_image_info.side_effect = Exception

        with pytest.raises(Exception) as exc:
            get_run_image(self.run, self.job_config, self.run_variables, self.docker_client)

        assert "Error while getting image information" in str(exc.value)

        assert self.run.add_to_log.call_count == 4
        assert "Run failed" in self.run.add_to_log.call_args_list[-1][0][0]
        assert self.run.to_failed.call_count == 1

    @patch("core.container.RegistryImageHelper.get_image_info")
    @patch("core.container.ContainerImageBuilder.get_image")
    def test_test_get_run_image_docker_exception(self, mock_get_image, mock_get_image_info):
        mock_get_image_info.return_value = Mock()
        mock_get_image.side_effect = RegistryContainerPullError

        result = get_run_image(self.run, self.job_config, self.run_variables, self.docker_client)

        assert result is None
        assert self.run.add_to_log.call_count == 5
        assert "Run failed" in self.run.add_to_log.call_args_list[-1][0][0]
        assert self.run.to_failed.call_count == 1

    @patch("core.container.RegistryImageHelper.get_image_info")
    @patch("core.container.ContainerImageBuilder.get_image")
    def test_test_get_run_image_exception(self, mock_get_image, mock_get_image_info):
        mock_get_image_info.return_value = Mock()
        mock_get_image.side_effect = Exception

        with pytest.raises(Exception) as exc:
            get_run_image(self.run, self.job_config, self.run_variables, self.docker_client)

        assert "Error while preparing the run image" in str(exc.value)

        assert self.run.add_to_log.call_count == 7
        assert "Run failed" in self.run.add_to_log.call_args_list[-1][0][0]
        assert self.run.to_failed.call_count == 1
