from django.contrib import admin

from package.models import ChunkedPackagePart, Package

# admin.site.register(Package)
admin.site.register(ChunkedPackagePart)


@admin.register(Package)
class PackageAdmin(admin.ModelAdmin):
    list_display = ["filename", "uuid", "short_uuid", "project", "created", "storage_location"]
    list_display_links = (
        "uuid",
        "short_uuid",
    )

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "short_uuid"]
