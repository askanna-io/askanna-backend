import json

from django.apps import apps
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.utils import timezone

from run.models import Run
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file


def add_key_to_unique_keys(key: dict, unique_keys: list) -> list:
    """Check if key is already in unique_keys list and add it if not. If the key is already in the list, update the
    count and data type if needed.

    Args:
        key (dict): key to add to unique_keys
        unique_keys (list): list of unique keys

    Returns:
        list: list of updated unique keys
    """

    add_key = True
    for unique_key in unique_keys:
        if key["name"] == unique_key["name"]:
            add_key = False
            if unique_key.get("count"):
                unique_key.update({"count": unique_key["count"] + 1})
            if key["type"] != unique_key["type"]:
                if key["type"] in ("integer", "float") and unique_key["type"] in ("integer", "float"):
                    unique_key.update({"type": "float"})
                else:
                    unique_key.update({"type": "mixed"})
            break

    if add_key:
        unique_keys.append(key)

    return unique_keys


def get_unique_names_with_data_type(all_keys: list) -> list:
    """
    Make a unique list of names in the list of dictionaries and set data type for each name

    `all_keys` is a list of dictionaries where each dictionary has two keys:
    - name
    - type

    The functon returns a list of dictionaries with unique names and the date type for each name. If data type values
    or not unique, it's set to 'mixed'.
    """
    unique_keys = []

    for key in all_keys:
        unique_keys = add_key_to_unique_keys(key, unique_keys)

    return unique_keys


def create_run_tracked_object_file_and_meta_dict(run: Run, type: str) -> tuple[File, dict] | tuple[None, None]:
    assert type in ("variable", "metric")

    model = apps.get_model("run", f"Run{type.capitalize()}")
    tracked_objects = model.objects.filter(run__suuid=run.suuid)

    if not tracked_objects:
        return None, None

    def compose_tracked_object(object, type):
        return {
            f"{type}": getattr(object, type),
            "label": object.label,
            "run_suuid": run.suuid,
            "created_at": object.created_at.isoformat(),
        }

    object_content_file = ContentFile(
        json.dumps([compose_tracked_object(object, type) for object in tracked_objects]).encode("utf-8"),
        name=f"{type}s.json",
    )

    object_file = File.objects.create(
        name=object_content_file.name,
        file=object_content_file,
        size=object_content_file.size,
        etag=get_md5_from_file(object_content_file),
        content_type=get_content_type_from_file(object_content_file),
        created_for=run,
        created_by=run.created_by_member,
        completed_at=timezone.now(),
    )

    count = len(tracked_objects)

    all_object_names = []
    all_label_names = []
    for object in tracked_objects:
        all_object_names.append(
            {
                "name": getattr(object, type).get("name"),
                "type": getattr(object, type).get("type"),
                "count": 1,
            }
        )

        labels = object.label
        if labels:
            for label in labels:
                all_label_names.append(
                    {
                        "name": label.get("name"),
                        "type": label.get("type"),
                    }
                )

    unique_object_names = get_unique_names_with_data_type(all_object_names)
    unique_label_names = get_unique_names_with_data_type(all_label_names) if all_label_names else None

    return object_file, {
        "count": count,
        f"{type}_names": unique_object_names,
        "label_names": unique_label_names,
    }


def update_run_metrics_file_and_meta(run: Run) -> None:
    """
    Update the metrics file, and meta information with count and unique metric_names and label_names
    """
    lock_key = f"run.RunMetric:update_file_and_meta:{run.suuid}"

    assert cache.get(lock_key) is None, "Run Metrics file and meta is already being updated"

    cache.set(lock_key, True, timeout=60)
    try:
        if run.metrics_file:
            run.metrics_file.delete()

        run.metrics_file, run.metrics_meta = create_run_tracked_object_file_and_meta_dict(run, "metric")

        run.save(
            update_fields=[
                "metrics_file",
                "metrics_meta",
                "modified_at",
            ]
        )
    finally:
        cache.delete(lock_key)


def update_run_variables_file_and_meta(run: Run) -> None:
    """
    Update the variables file, and meta information with count and unique variable_names and label_names
    """
    lock_key = f"run.RunVariable:update_file_and_meta:{run.suuid}"

    assert cache.get(lock_key) is None, "Run Variables file and meta is already being updated"

    cache.set(lock_key, True, timeout=60)
    try:
        if run.variables_file:
            run.variables_file.delete()

        run.variables_file, run.variables_meta = create_run_tracked_object_file_and_meta_dict(run, "variable")

        run.save(
            update_fields=[
                "variables_file",
                "variables_meta",
                "modified_at",
            ]
        )
    finally:
        cache.delete(lock_key)
