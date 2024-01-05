#!/bin/sh

# Allow showing realtime python prints to /dev/stdout
export PYTHONUNBUFFERED=1

run_or_fail_system_command() {
  # We open a subshell to execute the command and capture the last_status
  sh -c "$1"
  internal_last_status=$?

  if [ "$internal_last_status" -ne "0" ]; then
    # AskAnna runner detected a non-zero exit code on system commands we will not proceed with other system commands
    print_newline
    echo "Failure in an AskAnna system command"

    # The following line is for AskAnna Backend
    echo "AskAnna exit_code=${internal_last_status}"

    # exit with stame status as the crashed job
    exit $internal_last_status
  fi
}

print_newline() {
  echo ""
}

# This passage will only printed to console when there is actually an upgrade available
ASKANNA_VERSION=$(askanna --version)

if echo $ASKANNA_VERSION | grep -Eq 'A newer version of AskAnna is available.'; then
  echo "$ASKANNA_VERSION"
  echo "   Upgrading AskAnna CLI to the latest version"
  SILENT_INSTALL_ASKANNA=$(pip3 install -U askanna)
  UPGRADED_ASKANNA_VERSION=$(askanna --version)
  echo "   Installed new version of AskAnna CLI"
  print_newline
fi

askanna --version
print_newline

mkdir -p /code >/dev/null
echo "Loading code package into the run environment"
run_or_fail_system_command "askanna-run-utils get-package >/dev/null"
echo "Finished loading code package"

{% if run.payload %}
mkdir -p /input >/dev/null
echo "Loading payload into the run environment"
run_or_fail_system_command "askanna-run-utils get-payload >/dev/null"
echo "Finished loading payload"
{% else %}
echo "No payload"
{% endif %}

echo 'AskAnna is running job "{{ run.job.name }}" for project "{{ run.project.name }}"'
echo 'We are running on "run_{{ run.suuid }}"'
print_newline

# Navigate to the folder where code for the run is located
cd /code
last_status=0

#----------------------------------------------------
# Run the commands specified in the job configuration
#----------------------------------------------------
{% for command in commands %}

echo '$ {{ command.print_command | safe }}'
{{ command.command | safe }}

last_status=$?

if [ "$last_status" -ne "0" ]; then
  # AskAnna runner detected a non-zero exit code and proceed with finishing uploading the artifact right now.
  # We don't store the result, as this job will not have any valid results because of the crash we just detected

  print_newline
  echo "The run failed"

  print_newline
  echo "Saving artifact..."
  cd /code
  run_or_fail_system_command "askanna-run-utils push-artifact"

  # Make sure we have pushed the tracked metrics and variables as well
  run_or_fail_system_command "askanna-run-utils push-metrics --force"
  run_or_fail_system_command "askanna-run-utils push-variables --force"

  # The following line is used by the AskAnna Backend to log the exit code
  echo "AskAnna exit_code=${last_status}"

  # Exit with stame status as the crashed job
  exit $last_status

else
  print_newline
fi

{% endfor %}
#----------------------------------------------------
# End running the job commands
#----------------------------------------------------

echo "Saving artifact and result..."

# Make sure we are in the folder where code for the run is located
cd /code
run_or_fail_system_command "askanna-run-utils push-artifact"
run_or_fail_system_command "askanna-run-utils push-result"
run_or_fail_system_command "askanna-run-utils push-metrics --force"
run_or_fail_system_command "askanna-run-utils push-variables --force"

print_newline
echo "Run succeeded"
