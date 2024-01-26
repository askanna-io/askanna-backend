import pytest
from celery.exceptions import Retry
from django.core.cache import cache

from run.tasks import (
    delete_runs,
    update_run_metrics_file_and_meta,
    update_run_variables_file_and_meta,
)


def test_update_run_metrics_file_and_meta(test_runs):
    result = update_run_metrics_file_and_meta.delay(test_runs["run_2"].suuid)
    assert result.successful() is True


def test_update_run_metrics_file_and_meta_with_lock(test_runs):
    lock_key = f"run.RunMetric:update_file_and_meta:{test_runs['run_2'].suuid}"
    cache.set(lock_key, True, timeout=10)
    try:
        with pytest.raises(Retry):
            update_run_metrics_file_and_meta.delay(test_runs["run_2"].suuid)
    finally:
        cache.delete(lock_key)


def test_update_run_variables_file_and_meta(test_runs):
    result = update_run_variables_file_and_meta.delay(test_runs["run_2"].suuid)
    assert result.successful() is True


def test_update_run_variables_file_and_meta_with_lock(test_runs):
    lock_key = f"run.RunVariable:update_file_and_meta:{test_runs['run_2'].suuid}"
    cache.set(lock_key, True, timeout=10)
    try:
        with pytest.raises(Retry):
            update_run_variables_file_and_meta.delay(test_runs["run_2"].suuid)
    finally:
        cache.delete(lock_key)


def test_delete_runs(test_runs):
    result = delete_runs.delay()
    assert result.successful() is True
