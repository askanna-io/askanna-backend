#!/bin/bash
askanna --version

mkdir -p /input >/dev/null
mkdir -p /code >/dev/null

{% if pl %}
echo "Loading payload into the run environment"
askanna-run-utils get-payload >/dev/null
echo "Finished loading payload"
{% else %}
echo "Payload is not set"
{% endif %}

echo "Loading code package into the run environment"
askanna-run-utils get-package >/dev/null
echo "Finished loading code package"

# first navigate to the folder where user code is located
cd /code

echo 'AskAnna is running job "{{ jd.name }}" for project "{{ pr.name }}"'
echo 'We are running on "run_{{ jr.short_uuid }}"'

last_status=0

# going into user land
{% for command in commands %}
echo '$ {{ command.print_command|safe }}'
{{ command.command | safe }}

last_status=$?

if [ "$last_status" -ne "0" ]; then
  # AskAnna runner detected a non-zero exitcode and proceed with finishing uploading artificacts right now
  # we don't store the result, as this job will not have any valid results because of the crash we just detected

  echo ""
  echo "The run failed:"
  # The following line is for AskAnna backend
  echo "AskAnna exit_code=${last_status}"

  # let's store the artifact for this run and exit
  echo ""
  echo "Saving artifact..."
  cd /code
  askanna artifact add
  askanna-run-utils push-metrics --force

  # exit with stame status as the crashed job
  exit $last_status

else
  # when everything was fine, let's add an empty row in the result
  echo ""
fi

{% endfor %}
# end userland

echo "Saving result and artifact..."

# forcefull going back into code directory
cd /code
askanna-run-utils push-result
askanna artifact add
askanna-run-utils push-metrics --force
askanna-run-utils push-variables --force

echo ""
echo "Run succeeded"
