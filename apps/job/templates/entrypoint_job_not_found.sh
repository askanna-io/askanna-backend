#!/bin/bash
askanna --version

echo 'AskAnna is running job "{{ run.job.name }}" for project "{{ run.project.name }}"'
echo 'We are running on "run_{{ run.suuid }}"'
echo ""
echo 'AskAnna could not start the job "{{run.job.name}}" because the job is not defined in the "askanna.yml"'
echo "Read on https://docs.askanna.io/job/create-job/ how to configure a job."
echo ""
echo "The run failed"

# The following line is used by the AskAnna Backend to log the exit code
echo "AskAnna exit_code=1"
exit 1
