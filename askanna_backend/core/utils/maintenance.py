import datetime

from django.db.models.query import QuerySet
from django.utils import timezone

from .config import get_setting_from_database


def remove_objects(queryset, ttl_hours: int = 1):
    """
    queryset: Queryset containing all objects, also the ones not to delete
    ttl_hours: we only delete objects older than `ttl_hours` old.
    """
    if not isinstance(queryset, QuerySet):
        raise Exception("Given queryset is not a Django Queryset")

    remove_ttl = str(get_setting_from_database(name="OBJECT_REMOVAL_TTL_HOURS", default=ttl_hours))
    remove_ttl_mins = int(float(remove_ttl) * 60.0)

    older_than = timezone.now() - datetime.timedelta(minutes=remove_ttl_mins)

    for obj in queryset.filter(deleted__lte=older_than):
        obj.delete()
