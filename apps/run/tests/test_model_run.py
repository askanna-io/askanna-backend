def test_run_function__str__run_with_name(test_runs):
    assert str(test_runs["run_1"]) == f"test run 1 ({test_runs['run_1'].suuid})"


def test_run_function__str__run_with_no_name(test_runs):
    assert str(test_runs["run_2"]) == str(test_runs["run_2"].suuid)


def test_run_function_set_status(test_runs):
    assert test_runs["run_3"].status == "FAILED"
    modified_at_before = test_runs["run_3"].modified_at

    test_runs["run_3"].set_status("COMPLETED")
    assert test_runs["run_3"].status == "COMPLETED"
    assert test_runs["run_3"].modified_at > modified_at_before


def test_run_function_set_finished_at(test_runs):
    assert test_runs["run_4"].started_at is not None
    assert test_runs["run_4"].finished_at is None
    assert test_runs["run_4"].duration is None

    modified_at_before = test_runs["run_2"].modified_at
    test_runs["run_4"].set_finished_at()

    assert test_runs["run_4"].modified_at > modified_at_before
    assert test_runs["run_4"].started_at is not None
    assert test_runs["run_4"].finished_at is not None
    assert test_runs["run_4"].finished_at > test_runs["run_4"].started_at

    duration = (test_runs["run_4"].finished_at - test_runs["run_4"].started_at).seconds

    assert test_runs["run_4"].duration == duration
