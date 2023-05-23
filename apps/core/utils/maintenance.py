import datetime

from django.db.models.query import QuerySet
from django.utils import timezone

from core.utils.config import get_setting


def remove_objects(queryset: QuerySet, ttl_hours: float = 1):
    """
    Remove objects from the database that are older than `ttl_hours` hours.

    Args:
        queryset: Queryset containing all objects, also the ones not to delete
        ttl_hours: we only delete objects older than `ttl_hours`.
    """
    if not isinstance(queryset, QuerySet):
        raise Exception("Given queryset is not a Django Queryset")

    remove_ttl_hours = get_setting(name="OBJECT_REMOVAL_TTL_HOURS", return_type=float, default=ttl_hours)
    older_than = timezone.now() - datetime.timedelta(hours=remove_ttl_hours)

    for obj in queryset.filter(deleted_at__lte=older_than):
        obj.delete()
