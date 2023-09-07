from __future__ import annotations

import io

from django.core import signing
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.core.files.base import ContentFile
from django.db import models
from PIL import Image

from core.models import BaseModel
from core.permissions.askanna_roles import (
    ProjectAdmin,
    ProjectMember,
    ProjectNoMember,
    ProjectPublicViewer,
    ProjectViewer,
    WorkspaceAdmin,
    WorkspaceMember,
    WorkspaceNoMember,
    WorkspacePublicViewer,
    WorkspaceViewer,
    get_request_role,
    get_role_class,
    merge_role_permissions,
)
from project.models import Project
from storage.models import File
from workspace.models import Workspace

MSP_WORKSPACE = "WS"
MEMBERSHIPS = [(MSP_WORKSPACE, "Workspace")]
WS_MEMBER = "WM"
WS_ADMIN = "WA"
WS_VIEWER = "WV"
ROLES = ((WS_VIEWER, "viewer"), (WS_MEMBER, "member"), (WS_ADMIN, "admin"))

AVATAR_SPECS = {
    "icon": (60, 60),
    "small": (120, 120),
    "medium": (180, 180),
    "large": (240, 240),
}


class MemberProfile(BaseModel):
    name = models.CharField("Name", blank=True, max_length=255)
    job_title = models.CharField("Job title", blank=True, default="", max_length=255)

    _avatar_directory = None

    @property
    def avatar_files(self) -> models.QuerySet[File] | None:
        try:
            return self.objectreference.file_created_for.all()  # type: ignore
        except ObjectDoesNotExist:
            return None

    def delete_avatar_files(self) -> models.QuerySet[File] | None:
        try:
            return self.objectreference.file_created_for.all().delete()  # type: ignore
        except ObjectDoesNotExist:
            return None

    @property
    def avatar_directory(self):
        if self._avatar_directory is None:
            self._avatar_directory = (
                "avatars/" + self.suuid[:2].lower() + "/" + self.suuid[2:4].lower() + "/" + self.suuid
            )

        return self._avatar_directory

    def set_avatar(self, avatar_file, created_by=None):
        created_by = created_by or self

        self.delete_avatar_files()

        File.objects.create(
            name=avatar_file.name,
            file=avatar_file,
            upload_to=self.avatar_directory,
            created_for=self,
            created_by=created_by,
        )

        with Image.open(avatar_file) as image:
            for spec_name, spec_size in AVATAR_SPECS.items():
                with io.BytesIO() as tmp_file, image.copy() as tmp_image:
                    tmp_image.thumbnail(spec_size)
                    tmp_image.save(fp=tmp_file, format="png")

                    filename = f"{spec_name}.png"
                    File.objects.create(
                        name=filename,
                        file=ContentFile(tmp_file.getvalue(), name=filename),
                        upload_to=self.avatar_directory,
                        created_for=self,
                        created_by=created_by,
                    )

    class Meta(BaseModel.Meta):
        abstract = True


class MembershipQuerySet(models.QuerySet):
    def active_members(self):
        return self.filter(deleted_at__isnull=True)


class Membership(MemberProfile):
    """
    Membership holds the relation between
    - workspace vs user
    - project vs user
    """

    object_uuid = models.UUIDField(db_index=True)
    object_type = models.CharField(max_length=2, choices=MEMBERSHIPS)
    role = models.CharField(max_length=2, default=WS_MEMBER, choices=ROLES)
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

    @classmethod
    def get_roles_for_project(
        cls, user, project
    ) -> list[
        (
            type[ProjectAdmin]
            | type[ProjectMember]
            | type[ProjectViewer]
            | type[ProjectNoMember]
            | type[ProjectPublicViewer]
            | type[WorkspaceAdmin]
            | type[WorkspaceMember]
            | type[WorkspaceViewer]
            | type[WorkspaceNoMember]
            | type[WorkspacePublicViewer]
        )
    ]:
        workspace_role = cls.get_workspace_role(user, project.workspace)
        project_role = cls.get_project_role(user, project)
        roles = [workspace_role, project_role]

        if workspace_role.code == "WA" and ProjectAdmin not in roles:
            roles.append(ProjectAdmin)
        elif workspace_role.code == "WM" and ProjectMember not in roles:
            roles.append(ProjectMember)
        elif workspace_role.code == "WV" and ProjectViewer not in roles:
            roles.append(ProjectViewer)

        # Clean up the roles list. If multiple Project roles are present, remove the "lower" ones.
        if ProjectNoMember in roles and any(r in roles for r in [ProjectAdmin, ProjectMember, ProjectViewer]):
            roles.remove(ProjectNoMember)
        if ProjectAdmin in roles and ProjectMember in roles:
            roles.remove(ProjectMember)
        if ProjectAdmin in roles and ProjectViewer in roles:
            roles.remove(ProjectViewer)
        if ProjectMember in roles and ProjectViewer in roles:
            roles.remove(ProjectViewer)

        return roles

    @classmethod
    def get_project_membership(cls, user, project: Project) -> Membership | None:
        try:
            membership = cls.objects.get(
                object_uuid=str(project.uuid),
                object_type="PR",
                user=user,
                deleted_at__isnull=True,
            )
        except ObjectDoesNotExist:
            return None
        else:
            return membership

    @classmethod
    def get_project_role(
        cls, user, project: Project
    ) -> (
        type[ProjectAdmin]
        | type[ProjectMember]
        | type[ProjectViewer]
        | type[ProjectNoMember]
        | type[ProjectPublicViewer]
    ):
        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PRIVATE" or project.workspace.visibility == "PRIVATE"
        ):
            return ProjectNoMember

        if (user.is_anonymous or not user.is_active) and (
            project.visibility == "PUBLIC" and project.workspace.visibility == "PUBLIC"
        ):
            return ProjectPublicViewer

        membership = cls.get_project_membership(user, project)
        if membership:
            role = membership.get_role()
            if role in (ProjectAdmin, ProjectMember, ProjectViewer):
                return role

        if project.visibility == "PUBLIC" and project.workspace.visibility == "PUBLIC":
            return ProjectPublicViewer

        return ProjectNoMember

    @classmethod
    def get_workspace_membership(cls, user, workspace: Workspace) -> Membership | None:
        try:
            membership = cls.objects.get(
                object_uuid=str(workspace.uuid),
                object_type="WS",
                user=user,
                deleted_at__isnull=True,
            )
        except ObjectDoesNotExist:
            return None
        else:
            return membership

    @classmethod
    def get_workspace_role(
        cls, user, workspace: Workspace
    ) -> (
        type[WorkspaceAdmin]
        | type[WorkspaceMember]
        | type[WorkspaceViewer]
        | type[WorkspaceNoMember]
        | type[WorkspacePublicViewer]
    ):
        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PRIVATE":
            return WorkspaceNoMember
        if (user.is_anonymous or not user.is_active) and workspace.visibility == "PUBLIC":
            return WorkspacePublicViewer

        membership = cls.get_workspace_membership(user, workspace)
        if membership:
            role = membership.get_role()
            if role in (WorkspaceAdmin, WorkspaceMember, WorkspaceViewer):
                return role

        if workspace.visibility == "PUBLIC":
            return WorkspacePublicViewer

        return WorkspaceNoMember

    def get_role_serialized(self):
        """
        Role to be exposed to the outside
        """
        role = self.get_role()
        return {
            "code": role.code,
            "name": role.name,
        }

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

    def get_avatar_files(self):
        """
        Get avatar_files, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.avatar_files
        return self.avatar_files

    def to_deleted(self, removed_by=None):
        removed_by = removed_by or self

        if self.use_global_profile and self.user:
            # If use_global_profile is True, then make a copy of the global profile to the membership profile.
            self.name = self.user.name
            self.job_title = self.user.job_title
            self.use_global_profile = False
            self.save(
                update_fields=[
                    "name",
                    "job_title",
                    "use_global_profile",
                    "modified_at",
                ]
            )

            self.delete_avatar_files()
            user_avatar_files: models.QuerySet = self.user.avatar_files
            if isinstance(user_avatar_files, models.QuerySet) and user_avatar_files.count() > 0:
                for avatar_file in user_avatar_files:
                    with avatar_file.file as image_file:
                        File.objects.create(
                            name=avatar_file.name,
                            file=ContentFile(image_file.read(), name=avatar_file.name),
                            upload_to=self.avatar_directory,
                            created_for=self,
                            created_by=removed_by,
                        )

        super().to_deleted()

    def request_has_object_read_permission(self, request) -> bool:
        # User can always read its own membership as long as the membership is active
        if self.is_active and request.user == self.user:
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
            get_request_role(request)
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
