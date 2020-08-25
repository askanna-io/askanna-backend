import os
import django
from django.contrib.auth.models import Group

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_rest_permission.settings')
django.setup()


ROLES = ['admin', 'member']
MODELS = ['user', 'membership']

for role in ROLES:
    new_group, created = Group.objects.get_or_create(name=role)
