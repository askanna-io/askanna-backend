from django.contrib import admin

from package.models import Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "project",
        "created_at",
    ]
    date_hierarchy = "created_at"
    list_filter = (
        "created_at",
        "modified_at",
        "deleted_at",
    )
    search_fields = [
        "uuid",
        "suuid",
        "project__suuid",
        "project__name",
    ]
    fields = [
        "suuid",
        "project",
        "package_file",
        "modified_at",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "project",
        "package_file",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
