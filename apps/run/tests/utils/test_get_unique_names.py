from run.utils import get_unique_names_with_data_type


def test_get_unique_names_with_data_type():
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


def test_get_unique_names_with_data_type_empty():
    assert get_unique_names_with_data_type([]) == []


def test_get_unique_names_with_count():
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


def test_get_unique_names_with_data_type_float_and_integer():
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


def test_get_unique_names_with_data_type_mixed():
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
