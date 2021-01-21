#!/bin/bash
askanna --version

echo 'AskAnna is running for project "{{pr.name}}" and running on "{{pr.short_uuid}}"'

echo "AskAnna could not find the file: 'askanna.yml'"
echo "Read on https://docs.askanna.io/#/code?id=askannayml on how to create an 'askanna.yml' to configure a job."
echo ""
echo "Job failed"

# the following is for AskAnna only
echo "AskAnna exit_code=${last_status}"
exit 1
