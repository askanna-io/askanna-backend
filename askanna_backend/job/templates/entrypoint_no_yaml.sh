#!/bin/bash
askanna --version

echo 'AskAnna is running for project "{{pr.name}}" and running on "{{pr.short_uuid}}"'

echo "AskAnna could not start the job '{{jd.name}}'"
echo "Job '{{jd.name}}' not found in 'askanna.yml'"
echo "Read on https://docs.askanna.io/#/jobs?id=create-a-job on how to define a job.
echo "Job failed"

# the following is for AskAnna only
echo "AskAnna exit_code=${last_status}"
exit 1
