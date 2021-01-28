# -*- coding: utf-8 -*-
# Define a few enums that will represent options in the models.

# Environment Options  # noqa
ENV_CHOICES = (
    ("python2.7", "python2.7"),
    ("python3.5", "python3.5"),
    ("python3.6", "python3.6"),
    ("python3.7", "python3.7"),
)

# Status of a job execution  # noqa
JOB_STATUS = (
    ("SUBMITTED", "SUBMITTED"),
    ("COMPLETED", "COMPLETED"),
    ("PENDING", "PENDING"),
    ("PAUSED", "PAUSED"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("FAILED", "FAILED"),
    ("SUCCESS", "SUCCESS"),
)
