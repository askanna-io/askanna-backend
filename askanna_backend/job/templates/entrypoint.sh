#!/bin/bash
askanna --version

mkdir -p /input > /dev/null
mkdir -p /code > /dev/null

askanna payload > /dev/null
askanna package-download > /dev/null

# first navigate to the folder where user code is located
cd /code

echo 'AskAnna is running for project "{{pr.title}}" and running on "{{pr.short_uuid}}"'

last_status=0

# going into user land
{% for command in commands %}
echo '$ {{ command.print_command|safe }}'
{{ command.command|safe }}

last_status=$?

if [ $last_status -neq 0 ]
then
  # AskAnna runner detected a non-zero exitcode and proceed with finishing uploading artificacts right now
  # we don't store the result, as this job will not have any valid results because of the crash we just detected
  echo "AskAnna exit_code=${last_status}"

  # let's store the artifact for this run and exit
  askanna artifact

  # exit with stame status as the crashed job
  exit $last_status

else
  # when everything was fine, let's add an empty row in the result
  echo ""
fi

{% endfor %}
# end userland

echo "Saving results as artifact"

# forcefull going back into code directory
cd /code

askanna upload-result

askanna artifact

echo "Job succeeded"
