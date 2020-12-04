from django.contrib import admin, messages
from django.contrib.auth import admin as auth_admin
from django.contrib.auth import get_user_model
from django.utils.html import mark_safe, escape
from django.utils.translation import ugettext_lazy as _

from users.forms import UserChangeForm, UserCreationForm
from users.models import Membership, UserProfile, Invitation, PasswordResetLog
from users.serializers import PersonSerializer


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
        "object_uuid",
    ]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid"]

    def has_add_permission(self, request, obj=None):
        """ want to force users always to create memberships with user profile"""
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "user",
        "object_uuid",
    ]

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
                    _(
                        "Invitation sent to <strong>%(email)s</strong> for %(type)s %(workspace)s."
                    )
                    % {
                        "email": escape(invitation.email),
                        "type": invitation.object_type,
                        "workspace": invitation.object_uuid,
                    }
                ),
            )

    resend_invitation.short_description = _(
        "Resend invitation email for the given Invitations"
    )


@admin.register(PasswordResetLog)
class InvitationAdmin(admin.ModelAdmin):
    list_display = [
        "uuid",
        "email",
        "user",
        "front_end_domain",
        "remote_ip",
        "remote_host",
        "created",
    ]

    date_hierarchy = "created"
    list_filter = ("created", "modified", "deleted")
    search_fields = ["uuid", "email", "remote_ip"]
