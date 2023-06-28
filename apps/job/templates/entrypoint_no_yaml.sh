#!/bin/bash
askanna --version

echo 'AskAnna is running for project "{{pr.name}}" and running on "{{pr.suuid}}"'

echo "AskAnna could not find the file: 'askanna.yml'"
echo "Read on https://docs.askanna.io/code/#askannayml on how to create an 'askanna.yml' to configure a job."
echo ""
echo "Job failed"

# the following is for AskAnna only
echo "AskAnna exit_code=1"
exit 1
