from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.utils.html import escape, mark_safe
from users.forms import UserChangeForm, UserCreationForm
from users.models import Invitation, Membership, PasswordResetLog, UserProfile
from users.serializers import PersonSerializer

User = get_user_model()


# Don't show Auth Groups in the Django Admin because we don't use them.
admin.site.unregister(Group)


@admin.register(User)
class UserAdmin(auth_admin.UserAdmin):

    form = UserChangeForm
    add_form = UserCreationForm
    fieldsets = (("User", {"fields": ("name", "suuid")}),) + auth_admin.UserAdmin.fieldsets
    list_display = ["username", "name", "uuid", "suuid", "is_superuser"]
    search_fields = ["name", "uuid", "suuid"]


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "uuid",
        "user",
        "object_uuid",
        "role",
        "job_title",
        "created",
    ]

    raw_id_fields = ["user"]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]

    def get_queryset(self, request):
        """
        We don't want to list invites (user=None)
        """
        qs = super().get_queryset(request)
        return qs.filter(user__isnull=False)

    def has_add_permission(self, request, obj=None):  # pragma: no cover
        """want to force users always to create memberships with user profile"""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "suuid",
        "uuid",
        "user",
        "object_uuid",
        "role",
        "job_title",
        "created",
    ]

    raw_id_fields = ["user"]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "email",
        "object_uuid",
        "object_type",
    ]

    raw_id_fields = ["user"]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]

    actions = ["resend_invitation"]

    def resend_invitation(self, request, queryset):
        """Resend invitation email for the given Invitations."""
        if queryset.count() > 10:
            messages.error(
                request,
                "For performance reasons, no more than 10 invitations can be sent at once.",
            )
            return

        for invitation in queryset.all():
            PersonSerializer(invitation).send_invite()
            messages.success(
                request,
                mark_safe(
                    "Invitation sent to <strong>%(email)s</strong> for %(type)s %(workspace)s."
                    % {
                        "email": escape(invitation.email),
                        "type": invitation.object_type,
                        "workspace": invitation.object_uuid,
                    }
                ),
            )

    resend_invitation.short_description = "Resend invitation email for the given Invitations"


@admin.register(PasswordResetLog)
class PasswordResetLogAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "email",
        "user",
        "front_end_domain",
        "remote_ip",
        "remote_host",
        "created",
    ]

    raw_id_fields = ["user"]
    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "email", "remote_ip"]

    def has_add_permission(self, request, obj=None):  # pragma: no cover
        """disable adding logs manually, since that doesn't make sense"""
        return False
