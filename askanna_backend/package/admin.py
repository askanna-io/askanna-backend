from django.contrib import admin
from package.models import ChunkedPackagePart, Package


class ChunkedPackageInline(admin.TabularInline):
    model = ChunkedPackagePart
    fields = [
        "uuid",
        "filename",
        "size",
        "file_no",
        "is_last",
        "package",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = fields
    ordering = ["created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
        "name",
        "description",
        "original_filename",
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
    inlines = [ChunkedPackageInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
