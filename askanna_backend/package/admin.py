from django.contrib import admin

from package.models import ChunkedPackagePart, Package

# admin.site.register(Package)
admin.site.register(ChunkedPackagePart)


@admin.register(Package)
class JobDefAdmin(admin.ModelAdmin):
    list_display = ["filename", "uuid", "project", "created_at", "storage_location"]
    # list_display_links = (
    #     "name",
    #     "uuid",
    #     "short_uuid",
    # )

    date_hierarchy = "created_at"
    # list_filter = ("created", "modified", "deleted")
    # search_fields = ["uuid", "short_uuid"]
