from django.contrib import admin

from storage.models import File


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {"fields": ("uuid", "suuid")}),
        ("File info", {"fields": ("name", "description", "file", "created_for", "created_by")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "file",
        "created_for",
        "created_by",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    list_display = [
        "suuid",
        "name",
        "file",
        "created_for",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = [
        "created_at",
        "modified_at",
        "deleted_at",
    ]
    search_fields = [
        "uuid",
        "suuid",
        "name",
        "file",
    ]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "_created_for",
                "_created_for__account_user",
                "_created_by",
                "_created_by__account_user",
            )
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
