import pytest


@pytest.fixture()
def create_metric_dict():
    def _create_metric_dict(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [
                    {"name": "city", "value": "Amsterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                    {"name": "Missing data", "value": True, "type": "boolean"},
                    {"name": "Missing data tag", "type": "tag"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [
                    {"name": "city", "value": "Rotterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Quality", "value": "Good", "type": "string"},
                "label": [
                    {"name": "city", "value": "Rotterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Quality", "value": "Ok", "type": "string"},
                "label": [
                    {"name": "city", "value": "Amsterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                    {"name": "Missing data", "value": True, "type": "boolean"},
                    {"name": "Missing data tag", "type": "tag"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_metric_dict


@pytest.fixture()
def create_metric_dict_small() -> list[dict]:
    def _create_metric_dict(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_metric_dict


@pytest.fixture()
def create_metric_dict_small_no_label() -> list[dict]:
    def _create_metric_dict_small_no_label(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "metric": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_metric_dict_small_no_label


@pytest.fixture()
def create_variable_dict() -> list[dict]:
    def _create_variable_dict(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [
                    {"name": "city", "value": "Amsterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                    {"name": "Missing data", "value": True, "type": "boolean"},
                    {"name": "Missing data tag", "type": "tag"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [
                    {"name": "city", "value": "Rotterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Quality", "value": "Good", "type": "string"},
                "label": [
                    {"name": "city", "value": "Rotterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Quality", "value": "Ok", "type": "string"},
                "label": [
                    {"name": "city", "value": "Amsterdam", "type": "string"},
                    {"name": "product", "value": "TV", "type": "string"},
                    {"name": "Missing data", "value": True, "type": "boolean"},
                    {"name": "Missing data tag", "type": "tag"},
                ],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_variable_dict


@pytest.fixture()
def create_variable_dict_small() -> list[dict]:
    def _create_variable_dict_small(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [{"name": "city", "value": "Amsterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [{"name": "city", "value": "Rotterdam", "type": "string"}],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_variable_dict_small


@pytest.fixture()
def create_variable_dict_small_no_label() -> list[dict]:
    def _create_variable_dict_small_no_label(run_suuid: str) -> list[dict]:
        return [
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.623", "type": "integer"},
                "label": [],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
            {
                "run_suuid": run_suuid,
                "variable": {"name": "Accuracy", "value": "0.876", "type": "integer"},
                "label": [],
                "created_at": "2021-02-14T12:00:01.123456+00:00",
            },
        ]

    return _create_variable_dict_small_no_label
