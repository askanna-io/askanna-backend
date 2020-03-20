from django.contrib import admin

from package.models import ChunkedPackagePart, Package

admin.site.register(Package)
admin.site.register(ChunkedPackagePart)

