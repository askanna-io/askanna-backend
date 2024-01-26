from run.models import RunVariable


def test_run_variable_mask_secret_variables_with_no_label(test_runs):
    run = test_runs["run_1"]

    run_variable = RunVariable.objects.create(
        run=run,
        variable={
            "name": "SECRET_VARIABLE",
            "value": "secret_value",
            "type": "string",
        },
    )

    assert run_variable.run == run
    assert run_variable.variable.get("value") == "***masked***"
    assert {
        "name": "is_masked",
        "value": None,
        "type": "tag",
    } in run_variable.label

    run_variable.delete()


def test_run_variable_mask_secret_variables_with_label(test_runs):
    run = test_runs["run_1"]

    run_variable = RunVariable.objects.create(
        run=run,
        variable={
            "name": "PASSWORD_VARIABLE",
            "value": "secret_value",
            "type": "string",
        },
        label=[
            {
                "name": "is_masked",
                "type": "tag",
            }
        ],
    )

    assert run_variable.run == run
    assert run_variable.variable.get("value") == "***masked***"
    assert {
        "name": "is_masked",
        "type": "tag",
    } in run_variable.label

    run_variable.delete()


def test_run_variable_mask_secret_variables_with_is_masked_set(test_runs):
    run = test_runs["run_1"]

    run_variable = RunVariable.objects.create(
        run=run,
        variable={
            "name": "TOKEN_VARIABLE",
            "value": "secret_value",
            "type": "string",
        },
        is_masked=True,
    )

    assert run_variable.run == run
    assert run_variable.variable.get("value") == "***masked***"
    assert {
        "name": "is_masked",
        "value": None,
        "type": "tag",
    } in run_variable.label

    run_variable.delete()
