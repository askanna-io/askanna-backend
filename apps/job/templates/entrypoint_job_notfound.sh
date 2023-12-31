#!/bin/bash
askanna --version

echo 'AskAnna is running for project "{{pr.name}}" and running on "{{pr.suuid}}"'

echo "AskAnna could not start the job '{{jd.name}}'"
echo "Job '{{jd.name}}' not found in 'askanna.yml'"
echo "Read on https://docs.askanna.io/jobs/create-job/ on how to define a job."
echo "Job failed"

# the following is for AskAnna only
echo "AskAnna exit_code=1"
exit 1
