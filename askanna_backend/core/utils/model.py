from django.core.exceptions import FieldDoesNotExist


def field_is_of_type_char(model, field_name) -> bool:
    """Function to check if the field is of type CharField, or a class related to CharField.

    Args:
        model: The model to check the field on.
        field_name: The name of the field to check.

    Returns:
        bool: True if the field is of type char, False otherwise.
    """
    if "__" in field_name:
        for _ in range(len(field_name.split("__")) - 1):
            model = model._meta.get_field(field_name.split("__")[0]).related_model
            field_name = "__".join(field_name.split("__")[1:])

        if not model:
            # The field is not a related field, so we return False
            # This can happen when a field is annotated in the queryset, or when the field is referring to a JSONField.
            return False

    try:
        field_type = model._meta.get_field(field_name).get_internal_type()
    except FieldDoesNotExist:
        # A field does not have to exist on the model. For example when a field is annotated in the queryset.
        # In this case we set the field_type to UnknownField and we don't lower case the field.
        return False

    return field_type in (
        "CharField",
        "EmailField",
        "FilePathField",
        "SlugField",
        "TextField",
        "URLField",
    )
