from django.contrib import admin
from package.models import ChunkedPackagePart, Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "original_filename",
        "size",
        "project",
        "created_by",
        "created",
    ]
    list_display_links = (
        "suuid",
        "original_filename",
    )
    date_hierarchy = "created"
    list_filter = (
        "created",
        "modified",
        "deleted",
    )
    search_fields = [
        "uuid",
        "suuid",
        "project__suuid",
        "project__name",
    ]
    fields = [
        "suuid",
        "original_filename",
        "name",
        "description",
        "size",
        "project",
        "created_by",
        "member",
        "modified",
        "created",
        "finished",
        "deleted",
    ]
    readonly_fields = [
        "suuid",
        "original_filename",
        "size",
        "project",
        "created_by",
        "member",
        "modified",
        "created",
        "finished",
        "deleted",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ChunkedPackagePart)
class ChunkedPackagePartAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "filename",
        "package",
        "created_at",
    ]
    list_display_links = [
        "uuid",
        "filename",
    ]
    date_hierarchy = "created_at"
    list_filter = (
        "is_last",
        "created_at",
        "deleted_at",
    )
    search_fields = [
        "uuid",
        "package__uuid",
        "package__suuid",
        "package__original_filename",
    ]
    fields = [
        "filename",
        "size",
        "file_no",
        "is_last",
        "package",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
