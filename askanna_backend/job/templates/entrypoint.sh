#!/bin/bash

# first navigate to the folder where user code is located
cd /code

echo 'askanna-runner for project {pr.title} running on {pr.short_uuid}'

{% for command in commands %}
echo '{{ command.print_command|safe }}'
{{ command.command|safe }}
{% endfor %}
