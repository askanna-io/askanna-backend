import time

from django.conf import settings

from celery import shared_task
from celery.signals import (
    task_success,
    after_task_publish,
    task_postrun
)


@shared_task(bind=True)
def dummy_sleep(self, duration=1):
    print(f"Dummy sleeping for {duration}")
    time.sleep(duration)
    print("Finished Sleeping")
    return duration


@shared_task(bind=True)
def hello_world(self, duration):
    name = 'John'
    time.sleep(duration)
    print(f"Hello {name}!")
    print(f"You've been sleeping for {duration}")


@shared_task(bind=True)
def hello_novalue(self):
    print("This is a novalue thingy")
    time.sleep(2)
    print("Slept for 2 seconds")
    return "Goal"


@shared_task(bind=True)
def hello_retvalue(self, duration):
    name = 'John'
    time.sleep(duration)

    retvalue = f"Hello {name}!\nYou'vebeen sleeping for {duration}!"
    return retvalue


@shared_task(bind=True)
def hello_error(self, duration):
    name = 'John'
    time.sleep(duration)
    raise Exception(f"Well, {name} sleeping for {duration} is Foo!")


@shared_task(bind=True)
def hello_add(self, x, y):
    ret = x + y
    return ret


@shared_task(bind=True)
def hello_part1(self, duration):
    print("In part 1 we increase the duration")
    new_duration = duration * 2
    return new_duration


@shared_task(bind=True)
def hello_part2(self, sleeptime=1):
    print("We are now going to sleep")
    print(f"We will be sleeping for: {sleeptime}")
    time.sleep(sleeptime)
    print("Finished our nap!")
    return "rested for {}".format(sleeptime)


@shared_task(bind=True)
def hello_part3(self, novalue=24):
    print("Another chained job")
    print(f"Having the value of: {novalue}")
    return "Playing for {}".format(novalue)


@shared_task(bind=True)
def hello_dictionary_part1(self, somedict={}):
    print("PART 1: accept dict")
    print("PART 1: received {}".format(somedict.keys()))
    somedict.update({"goal": "success"})
    print("PART 1: returns expanded dict!")
    return somedict


@shared_task(bind=True)
def hello_dictionary_part2(self, somedict={}):
    print("PART 2: received dict")
    print("PART 2: recived {}".format(somedict.keys()))
    print("PART 2: doing some processing...")
    time.sleep(2)
    somedict.update({"slept": 99})
    return somedict


@shared_task(bind=True)
def log_error(self, content=None):
    print("Something went wrong")
    print("We got {}".format(content))


@shared_task(bind=True)
def test_chain_error_part1(self):
    print("PART 1: will raise Exception")
    raise Exception("Something bad in part 1")


@shared_task(bind=True)
def test_chain_error_part2(self):
    print("PART 2: will raise Exception")
    raise Exception("Something bad in part 2")


@shared_task(bind=True)
def func_with_type(self, duration: int):
    print("Function with type checking")
    duration += 5
    print(f"Increased duration to: {duration}")
    return duration
