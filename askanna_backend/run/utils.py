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
