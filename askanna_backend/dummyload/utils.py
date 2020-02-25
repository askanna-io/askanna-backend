import time
from memory_profiler import memory_usage

import logging
celery_logger = logging.getLogger('celery')

def track_celery(method):
    """
    taken from: https://gist.github.com/hanneshapke/69f62e9df9da3b84bfc357cc75d248e8

    This decorator measures the execution time and memory usage of celery
    tasks. Decorate any celery task with the decorator and the results will
    be saved in a celery logger.

    Requirements:
    - pip install memory_profiler
    - a configured Django logger with the name 'celery'

    Usage:

    Decorate your functions like this:

    @track_celery
    @shared_task
    def my_long_running_and_mem_consuming_function():
        ...

    Results in your celery.log file (example):
        2020-02-02 14:05:05,700 [INFO]:
            my_long_running_and_mem_consuming_function completed
            in 011.36 sec with max mem: 98.67 MB
    """

    def measure_task(*args, **kwargs):
        start_time_of_task = time.time()
        mem_usage, result = memory_usage(
            (method, args, kwargs), retval=True, max_usage=True)
        result = method.delay(*args, **kwargs)
        end_time_of_task = time.time()

        celery_logger.info(
            '{} completed in {:06.2f} sec with max mem: {:8.2f} MB'.format(
                method.__name__,
                end_time_of_task - start_time_of_task,
                mem_usage)
        )
        return result

    return measure_task
