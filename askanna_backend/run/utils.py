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
