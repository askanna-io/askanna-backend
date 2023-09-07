from rest_framework import permissions


class AskAnnaPermission(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            method_name = "request_has_object_read_permission"
        else:
            method_name = "request_has_object_write_permission"

        assert hasattr(
            obj, method_name
        ), f"Model '{obj._meta.app_label}.{obj._meta.object_name}' does not have a method '{method_name}'."

        return getattr(obj, method_name)(request)
