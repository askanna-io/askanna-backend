import json
from unittest.mock import Mock, patch

import pytest

from run.redis import RedisRunLogQueue


@patch("redis.Redis.from_url")
@patch("run.redis.logger")
def test_redis_run_log_queue_add_with_print_log(mock_logger, mock_redis):
    mock_redis.return_value.llen.return_value = 0
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        assert log_queue.log_idx == 0

        message = "test_message"
        timestamp = "2022-01-01T00:00:00"
        print_log = True

        log_queue.add(message, timestamp, print_log)

        assert log_queue.log_idx == 1
        mock_redis.return_value.rpush.assert_called_once_with(
            log_queue.redis_queue_name, json.dumps([1, timestamp, message])
        )
        mock_logger.info.assert_called_once_with([1, timestamp, message])
    finally:
        log_queue.remove()


@patch("redis.Redis.from_url")
@patch("run.redis.logger")
def test_redis_run_log_queue_add_without_print_log(mock_logger, mock_redis):
    mock_redis.return_value.llen.return_value = 0
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        assert log_queue.log_idx == 0

        message = "test_message"
        timestamp = "2022-01-01T00:00:00"
        print_log = False

        log_queue.add(message, timestamp, print_log)

        assert log_queue.log_idx == 1
        mock_redis.return_value.rpush.assert_called_once_with(
            log_queue.redis_queue_name, json.dumps([1, timestamp, message])
        )
        mock_logger.info.assert_not_called()
    finally:
        log_queue.remove()


@patch("django.utils.timezone.now")
@patch("redis.Redis.from_url")
@patch("run.redis.logger")
def test_redis_run_log_queue_add_without_timestamp(mock_logger, mock_redis, mock_timestamp):
    mock_redis.return_value.llen.return_value = 0
    timestamp = "2023-01-01T00:00:00"
    mock_timestamp.return_value.isoformat.return_value = timestamp
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        assert log_queue.log_idx == 0

        message = "test_message"

        log_queue.add(message)

        assert log_queue.log_idx == 1
        mock_redis.return_value.rpush.assert_called_once_with(
            log_queue.redis_queue_name, json.dumps([1, timestamp, message])
        )
        mock_logger.info.assert_not_called()
    finally:
        log_queue.remove()


@patch("redis.Redis.from_url")
def test_redis_run_log_queue_get(mock_redis):
    mock_redis.return_value.llen.return_value = 2
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        mock_redis.return_value.lrange.return_value = [
            b'[1, "2024-01-01T00:00:00", "test_message_1"]',
            b'[2, "2024-01-01T00:00:01", "test_message_2"]',
        ]
        assert log_queue.get() == [
            [1, "2024-01-01T00:00:00", "test_message_1"],
            [2, "2024-01-01T00:00:01", "test_message_2"],
        ]

    finally:
        log_queue.remove()


@patch("redis.Redis.from_url")
def test_redis_run_log_queue_write_to_file(mock_redis):
    mock_redis.return_value.llen.return_value = 2
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        mock_redis.return_value.lrange.return_value = [
            b'[1, "2024-01-01T00:00:00", "test_message_1"]',
            b'[2, "2024-01-01T00:00:01", "test_message_2"]',
        ]

        log_queue.write_to_file()

    finally:
        log_queue.remove()


@patch("django.core.cache.cache.get")
@patch("redis.Redis.from_url")
def test_redis_run_log_queue_write_to_file_with_cache_key(mock_redis, mock_cache_get):
    mock_redis.return_value.llen.return_value = 2
    run = Mock()
    run.suuid = "test_suuid"

    try:
        log_queue = RedisRunLogQueue(run)

        mock_redis.return_value.lrange.return_value = [
            b'[1, "2024-01-01T00:00:00", "test_message_1"]',
            b'[2, "2024-01-01T00:00:01", "test_message_2"]',
        ]
        mock_cache_get.return_value = True

        # Expecting an assertion error
        with pytest.raises(AssertionError):
            log_queue.write_to_file()

        log_queue.write_to_file(force=True, force_max_retries=1)

    finally:
        log_queue.remove()


@patch("redis.Redis.from_url")
def test_redis_run_log_queue_write_to_file_without_existing_log_file(mock_redis, test_runs):
    mock_redis.return_value.llen.return_value = 2

    run = test_runs["run_1"]
    run.log_file = None

    try:
        log_queue = RedisRunLogQueue(run)

        mock_redis.return_value.lrange.return_value = [
            b'[1, "2024-01-01T00:00:00", "test_message_1"]',
            b'[2, "2024-01-01T00:00:01", "test_message_2"]',
        ]

        log_queue.write_to_file()

    finally:
        log_queue.remove()
