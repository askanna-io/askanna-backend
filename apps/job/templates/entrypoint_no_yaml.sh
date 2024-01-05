#!/bin/bash
askanna --version

echo 'AskAnna is running job "{{ run.job.name }}" for project "{{ run.project.name }}"'
echo 'We are running on "run_{{ run.suuid }}"'
echo ""
echo 'AskAnna could not find the file: "askanna.yml"'
echo 'Read on https://docs.askanna.io/code/#askannayml how to create an "askanna.yml" to configure a job.''
echo ""
echo "The run failed"

# The following line is used by the AskAnna Backend to log the exit code
echo "AskAnna exit_code=1"
exit 1
