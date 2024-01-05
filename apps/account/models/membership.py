from __future__ import annotations

from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from django.utils import timezone

from core.models import BaseModel
from core.permissions.role_utils import (
    get_role_class,
    get_user_role,
    merge_role_permissions,
)
from core.permissions.roles import (
    ProjectAdmin,
    ProjectMember,
    ProjectViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceViewer,
)
from storage.models import File
from storage.utils.file import get_content_type_from_file, get_md5_from_file
from workspace.models import Workspace

MSP_WORKSPACE = "WS"
MEMBERSHIPS = [(MSP_WORKSPACE, "Workspace")]

ROLES = (
    (WorkspaceViewer.code, WorkspaceViewer.name),
    (WorkspaceMember.code, WorkspaceMember.name),
    (WorkspaceAdmin.code, WorkspaceAdmin.name),
)


class MemberProfile(BaseModel):
    name = models.CharField("Name", blank=True, max_length=255)
    job_title = models.CharField("Job title", blank=True, default="", max_length=255)
    avatar_file = models.OneToOneField("storage.File", on_delete=models.SET_NULL, null=True)

    @property
    def upload_directory(self):
        return f"avatars/{self.suuid[:2].lower()}/{self.suuid[2:4].lower()}/{self.suuid}"

    def set_avatar(self, avatar_file: ContentFile, created_by=None):
        created_by = created_by or self

        self.delete_avatar_file()

        self.avatar_file = File.objects.create(
            name=avatar_file.name,
            file=avatar_file,
            size=avatar_file.size,
            etag=get_md5_from_file(avatar_file),
            content_type=get_content_type_from_file(avatar_file),
            created_for=self,
            created_by=created_by,
            completed_at=timezone.now(),
        )

        self.save(update_fields=["avatar_file", "modified_at"])

    def delete_avatar_file(self):
        if self.avatar_file:
            self.avatar_file.delete()
            self.avatar_file = None
            self.save(update_fields=["avatar_file", "modified_at"])

    def delete(self, using=None, keep_parents=False):
        self.delete_avatar_file()
        super().delete(using=using, keep_parents=keep_parents)

    class Meta(BaseModel.Meta):
        abstract = True


class MembershipQuerySet(models.QuerySet):
    def active_members(self):
        return self.filter(deleted_at__isnull=True)

    def active_admins(self):
        return self.active_members().filter(role=WorkspaceAdmin.code)

    def get_workspace_membership(self, user, workspace: Workspace) -> Membership | None:
        try:
            return self.active_members().get(
                object_uuid=workspace.uuid,
                object_type=MSP_WORKSPACE,
                user=user,
            )
        except ObjectDoesNotExist:
            return None


class Membership(MemberProfile):
    """
    Membership holds the relation between workspace & user
    """

    object_uuid = models.UUIDField(db_index=True)
    object_type = models.CharField(max_length=2, choices=MEMBERSHIPS)
    role = models.CharField(max_length=2, default=WorkspaceMember.code, choices=ROLES)
    user = models.ForeignKey(
        "account.User",
        on_delete=models.CASCADE,
        related_name="memberships",
        related_query_name="membership",
        blank=True,
        null=True,
    )

    use_global_profile = models.BooleanField(
        "Use AskAnna profile",
        default=True,
        help_text="Use information from the global user account",
    )

    objects = MembershipQuerySet().as_manager()

    @property
    def is_active(self):
        return self.deleted_at is None

    @property
    def workspace(self):
        if self.object_type == MSP_WORKSPACE:
            return cache.get_or_set(
                f"membership_workspace_{self.object_uuid}",
                lambda: Workspace.objects.get(uuid=self.object_uuid),
                timeout=10,
            )
        return None

    def get_status(self) -> str:
        if self.user and not self.deleted_at:
            return "active"
        if self.deleted_at:
            return "deleted"
        if getattr(self, "invitation", None):
            return "invited"
        return "blocked"

    def get_role(
        self,
    ) -> (
        type[WorkspaceAdmin]
        | type[WorkspaceMember]
        | type[WorkspaceViewer]
        | type[ProjectAdmin]
        | type[ProjectMember]
        | type[ProjectViewer]
    ):
        role = get_role_class(self.role)
        if role in (WorkspaceAdmin, WorkspaceMember, WorkspaceViewer, ProjectAdmin, ProjectMember, ProjectViewer):
            return role

        raise ValueError(f"Unknown membership role: {self.role}")

    def __str__(self):
        if self.get_name():
            return f"{self.get_name()} ({self.suuid})"
        return self.suuid

    def get_name(self) -> str | None:
        """
        Get name, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.name
        return self.name

    def get_job_title(self) -> str | None:
        """
        Get job_title, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.job_title
        return self.job_title

    def get_avatar_file(self):
        """
        Get avatar_file, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.avatar_file
        return self.avatar_file

    def to_deleted(self, removed_by=None):
        removed_by = removed_by or self

        if self.use_global_profile and self.user:
            # If use_global_profile is True, then make a copy of the global profile to the membership profile.
            self.name = self.user.name
            self.job_title = self.user.job_title
            self.use_global_profile = False

            self.delete_avatar_file()

            if self.user.avatar_file:
                with self.user.avatar_file.file.open() as image_file:
                    self.avatar_file = File.objects.create(
                        name=self.user.avatar_file.name,
                        file=ContentFile(image_file.read(), name=self.user.avatar_file.name),
                        created_for=self,
                        created_by=removed_by,
                    )

            self.save(
                update_fields=[
                    "name",
                    "job_title",
                    "avatar_file",
                    "use_global_profile",
                    "modified_at",
                ]
            )

        super().to_deleted()

    def request_has_object_read_permission(self, request, view) -> bool:
        # User can always read its own membership as long as the membership is active
        if request.user and request.user == self.user and self.is_active:
            return True

        # No read permission if membership is set to use the global user profile
        if self.use_global_profile:
            return False

        # Read permission to this membership is given if the workspace visibility is PUBLIC
        # Note: for reproducibility reasons we show the membership also if the membership is inactive.
        if self.workspace and self.workspace.is_public:
            return True

        if request.user.is_anonymous:
            return False

        # Read permission to this membership is given if the request.user has an active membership for this
        # membership's workspace with the role permission "workspace.info.view"
        request_user_membership = request.user.active_memberships.filter(
            object_uuid=self.object_uuid, object_type=MSP_WORKSPACE
        )

        request_user_roles = list({membership.get_role() for membership in request_user_membership}) + [
            get_user_role(request.user)
        ]

        return merge_role_permissions(request_user_roles).get("workspace.info.view", False)

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["user", "object_uuid", "object_type", "deleted_at"]]


class Invitation(Membership):
    email = models.EmailField(blank=False)

    @property
    def token_signer(self):
        return signing.TimestampSigner()

    def generate_token(self):
        return self.token_signer.sign(self.suuid)
