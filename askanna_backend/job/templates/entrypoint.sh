#!/bin/bash
askanna --version

mkdir -p /input > /dev/null
mkdir -p /code > /dev/null

askanna payload > /dev/null
askanna package-download > /dev/null

# first navigate to the folder where user code is located
cd /code

echo 'askanna-runner for project "{{pr.title}}" running on "{{pr.short_uuid}}"'

# going into user land
{% for command in commands %}
echo '$ {{ command.print_command|safe }}'
{{ command.command|safe }}
{% endfor %}
# end userland

echo "Saving results as artifact"

# forcefull going back into code directory
cd /code

askanna artifact

echo "Job finished"
