from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.models import Group
from django.utils.html import escape
from django.utils.safestring import mark_safe

from account.models.membership import Invitation, Membership, UserProfile
from account.models.user import PasswordResetLog, User
from account.serializers.people import InviteSerializer

# Don't show Auth Groups in the Django Admin because we don't use them.
admin.site.unregister(Group)


class MembershipInline(admin.TabularInline):
    model = Membership
    show_change_link = True
    fields = [
        "suuid",
        "object_type",
        "object_uuid",
        "role",
        "created_at",
        "deleted_at",
    ]
    readonly_fields = [
        "suuid",
        "object_type",
        "object_uuid",
        "created_at",
        "deleted_at",
    ]
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "username",
        "name",
        "created_at",
        "is_active",
        "is_superuser",
    ]
    search_fields = ["name", "email", "username", "uuid", "suuid"]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_filter = ["created_at", "modified_at", "deleted_at", "is_active", "is_superuser", "is_staff"]

    fieldsets = (
        (None, {"fields": ("suuid", "username")}),
        ("Personal info", {"fields": ("email", "name", "job_title")}),
        ("User status", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Dates", {"fields": ("last_login", "modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "last_login",
        "modified_at",
        "created_at",
        "deleted_at",
    ]

    inlines = [MembershipInline]

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "user",
        "object_type",
        "object_uuid",
        "role",
        "created_at",
        "deleted_at",
    ]
    search_fields = ["uuid", "suuid", "user__email", "user__name", "user__suuid"]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_filter = ("created_at", "modified_at", "deleted_at", "role", "object_type")

    fieldsets = (
        (None, {"fields": ("suuid",)}),
        ("Membership info", {"fields": ("user", "object_type", "object_uuid", "role")}),
        ("User profile", {"fields": ("use_global_profile", "name", "job_title")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "created_at",
        "modified_at",
        "deleted_at",
        "user",
        "object_type",
        "object_uuid",
        "use_global_profile",
        "name",
        "job_title",
    ]
    raw_id_fields = ["user"]

    def get_queryset(self, request):
        """
        We don't want to list invites (user=None)
        """
        qs = super().get_queryset(request)
        return qs.filter(user__isnull=False)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "user",
        "object_type",
        "object_uuid",
        "name",
        "job_title",
        "created_at",
        "deleted_at",
    ]
    search_fields = ["uuid", "suuid", "user__email", "user__name", "user__suuid"]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_filter = ("created_at", "modified_at", "deleted_at")

    fieldsets = (
        (None, {"fields": ("suuid",)}),
        ("Membership info", {"fields": ("user", "object_type", "object_uuid", "role")}),
        ("User profile", {"fields": ("use_global_profile", "name", "job_title")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "created_at",
        "modified_at",
        "deleted_at",
    ]
    raw_id_fields = ["user"]

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "email",
        "object_type",
        "object_uuid",
        "role",
        "created_at",
        "deleted_at",
    ]
    search_fields = ["uuid", "suuid", "email"]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_filter = ("created_at", "modified_at", "deleted_at")

    actions = ["resend_invitation"]

    fieldsets = (
        (None, {"fields": ("suuid",)}),
        ("Membership info", {"fields": ("object_type", "object_uuid", "role")}),
        ("Invite info", {"fields": ("email", "front_end_url")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "suuid",
        "created_at",
        "modified_at",
        "deleted_at",
    ]

    def resend_invitation(self, request, queryset):
        """Resend invitation email for the given Invitations."""
        if queryset.count() > 10:
            messages.error(
                request,
                "For performance reasons, no more than 10 invitations can be sent at once.",
            )
            return

        for invitation in queryset.all():
            InviteSerializer(invitation).send_invite(front_end_url=settings.ASKANNA_UI_URL)
            messages.success(
                request,
                mark_safe(  # nosec: B703, B308
                    f"Invitation sent to <strong>{escape(invitation.email)}</strong> for {invitation.object_type} "
                    f"{invitation.object_uuid}."
                ),
            )

    resend_invitation.short_description = "Resend selected invitations"


@admin.register(PasswordResetLog)
class PasswordResetLogAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "email",
        "user",
        "front_end_domain",
        "remote_ip",
        "remote_host",
        "created_at",
    ]
    search_fields = ["uuid", "email", "remote_ip", "user__email", "user__name", "user__suuid"]
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_filter = ("created_at", "modified_at", "deleted_at")

    fieldsets = (
        (None, {"fields": ("suuid",)}),
        ("Reset info", {"fields": ("email", "front_end_domain", "remote_ip", "remote_host", "meta")}),
        ("Dates", {"fields": ("modified_at", "created_at", "deleted_at")}),
    )
    readonly_fields = [
        "uuid",
        "suuid",
        "created_at",
        "modified_at",
        "deleted_at",
        "email",
        "front_end_domain",
        "remote_ip",
        "remote_host",
        "meta",
    ]
    raw_id_fields = ["user"]

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
