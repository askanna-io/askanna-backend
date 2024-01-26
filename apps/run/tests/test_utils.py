import pytest
from django.core.cache import cache

from run.utils import (
    get_unique_names_with_data_type,
    update_run_metrics_file_and_meta,
    update_run_variables_file_and_meta,
)


class TestGetUniqueNamesWithDataType:
    def test_get_unique_names_with_data_type(self):
        assert get_unique_names_with_data_type(
            [
                {
                    "name": "foo",
                    "type": "string",
                },
                {
                    "name": "bar",
                    "type": "string",
                },
                {
                    "name": "foo",
                    "type": "string",
                },
            ]
        ) == [
            {
                "name": "foo",
                "type": "string",
            },
            {
                "name": "bar",
                "type": "string",
            },
        ]

    def test_get_unique_names_with_data_type_empty(self):
        assert get_unique_names_with_data_type([]) == []

    def test_get_unique_names_with_count(self):
        assert get_unique_names_with_data_type(
            [
                {
                    "name": "foo",
                    "type": "string",
                    "count": 1,
                },
                {
                    "name": "bar",
                    "type": "string",
                    "count": 1,
                },
                {
                    "name": "foo",
                    "type": "string",
                    "count": 1,
                },
            ],
        ) == [
            {
                "name": "foo",
                "type": "string",
                "count": 2,
            },
            {
                "name": "bar",
                "type": "string",
                "count": 1,
            },
        ]

    def test_get_unique_names_with_data_type_float_and_integer(self):
        assert get_unique_names_with_data_type(
            [
                {
                    "name": "foo",
                    "type": "integer",
                    "count": 1,
                },
                {
                    "name": "bar",
                    "type": "string",
                    "count": 1,
                },
                {
                    "name": "foo",
                    "type": "float",
                    "count": 1,
                },
            ],
        ) == [
            {
                "name": "foo",
                "type": "float",
                "count": 2,
            },
            {
                "name": "bar",
                "type": "string",
                "count": 1,
            },
        ]

    def test_get_unique_names_with_data_type_mixed(self):
        assert get_unique_names_with_data_type(
            [
                {
                    "name": "foo",
                    "type": "integer",
                    "count": 1,
                },
                {
                    "name": "bar",
                    "type": "string",
                    "count": 1,
                },
                {
                    "name": "foo",
                    "type": "string",
                    "count": 1,
                },
            ],
        ) == [
            {
                "name": "foo",
                "type": "mixed",
                "count": 2,
            },
            {
                "name": "bar",
                "type": "string",
                "count": 1,
            },
        ]


class TestUpdateRunMetricsFileAndMeta:
    def test_update_run_metrics_file_and_meta(self, test_runs, test_run_metrics):
        run = test_runs["run_2"]

        run.refresh_from_db()
        assert run.metrics_file is None
        assert run.metrics_meta is None

        update_run_metrics_file_and_meta(run)

        run.refresh_from_db()
        assert run.metrics_file is not None
        assert run.metrics_meta.get("count") == 4

        file_suuid = run.metrics_file.suuid
        update_run_metrics_file_and_meta(run)
        run.refresh_from_db()
        assert run.metrics_file.suuid != file_suuid

    def test_run_without_metrics_with_labels(self, test_runs, test_run_metrics):
        run = test_runs["run_4"]

        run.refresh_from_db()
        assert run.metrics_file is None
        assert run.metrics_meta is None

        update_run_metrics_file_and_meta(run)

        run.refresh_from_db()
        assert run.metrics_file is not None
        assert run.metrics_meta.get("count") == 2
        assert run.metrics_meta.get("labels") is None

    def test_run_without_metrics(self, test_runs):
        run = test_runs["run_1"]

        run.refresh_from_db()
        assert run.metrics_file is None
        assert run.metrics_meta is None

        update_run_metrics_file_and_meta(run)

        run.refresh_from_db()
        assert run.metrics_file is None
        assert run.metrics_meta is None

    def test_update_with_lock_key_set(self, test_runs, test_run_metrics):
        run = test_runs["run_2"]

        lock_key = f"run.RunMetric:update_file_and_meta:{run.suuid}"
        cache.set(lock_key, True, timeout=10)

        with pytest.raises(AssertionError) as exc_info:
            update_run_metrics_file_and_meta(run)

        assert str(exc_info.value) == "Run Metrics file and meta is already being updated"

        cache.delete(lock_key)


class TestUpdateRunVariablesFileAndMeta:
    def test_update_run_variables_file_and_meta(self, test_runs, test_run_variables):
        run = test_runs["run_2"]

        run.refresh_from_db()
        assert run.variables_file is None
        assert run.variables_meta is None

        update_run_variables_file_and_meta(run)

        run.refresh_from_db()
        assert run.variables_file is not None
        assert run.variables_meta.get("count") == 4

        file_suuid = run.variables_file.suuid
        update_run_variables_file_and_meta(run)
        run.refresh_from_db()
        assert run.variables_file.suuid != file_suuid

    def test_run_without_variables_with_labels(self, test_runs, test_run_variables):
        run = test_runs["run_4"]

        run.refresh_from_db()
        assert run.variables_file is None
        assert run.variables_meta is None

        update_run_variables_file_and_meta(run)

        run.refresh_from_db()
        assert run.variables_file is not None
        assert run.variables_meta.get("count") == 2
        assert run.variables_meta.get("labels") is None

    def test_run_without_variables(self, test_runs):
        run = test_runs["run_1"]

        run.refresh_from_db()
        assert run.variables_file is None
        assert run.variables_meta is None

        update_run_variables_file_and_meta(run)

        run.refresh_from_db()
        assert run.variables_file is None
        assert run.variables_meta is None

    def test_update_with_lock_key_set(self, test_runs, test_run_variables):
        run = test_runs["run_2"]

        lock_key = f"run.RunVariable:update_file_and_meta:{run.suuid}"
        cache.set(lock_key, True, timeout=10)

        with pytest.raises(AssertionError) as exc_info:
            update_run_variables_file_and_meta(run)

        assert str(exc_info.value) == "Run Variables file and meta is already being updated"

        cache.delete(lock_key)
