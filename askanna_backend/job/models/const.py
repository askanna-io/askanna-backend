# Define a few enums that will represent options in the models.

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
