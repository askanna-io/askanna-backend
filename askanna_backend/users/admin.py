from django.contrib import admin
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model

from askanna_backend.users.forms import UserChangeForm, UserCreationForm

from users.models import Membership

User = get_user_model()


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (
        ("User", {"fields": ("name", "short_uuid")}),
    ) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "name", "uuid", "short_uuid", "is_superuser"]
    search_fields = ["name", "uuid", "short_uuid"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "user",
        "role",
        "object_uuid",
    ]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]
