from django.contrib import admin
from package.models import ChunkedPackagePart, Package


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = [
        "short_uuid",
        "original_filename",
        "size",
        "project",
        "created_by",
        "created",
    ]
    list_display_links = (
        "short_uuid",
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
        "short_uuid",
        "project__short_uuid",
        "project__name",
    ]
    fields = [
        "short_uuid",
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
        "short_uuid",
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
        "package__short_uuid",
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
