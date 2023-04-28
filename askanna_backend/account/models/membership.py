from __future__ import annotations

from django.core import signing
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from account.models.avatar import BaseAvatarModel
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
    get_role_class,
)
from project.models import Project
from workspace.models import Workspace

MSP_PROJECT = "PR"
MSP_WORKSPACE = "WS"
MEMBERSHIPS = ((MSP_PROJECT, "Project"), (MSP_WORKSPACE, "Workspace"))
WS_MEMBER = "WM"
WS_ADMIN = "WA"
WS_VIEWER = "WV"
ROLES = ((WS_VIEWER, "viewer"), (WS_MEMBER, "member"), (WS_ADMIN, "admin"))


class MemberQuerySet(models.QuerySet):
    def active_members(self):
        return self.filter(deleted_at__isnull=True)

    def admins(self):
        return self.active_members().filter(role=WS_ADMIN)

    def members(self):
        """
        Members include admins
        """
        return self.active_members()

    def all_admins(self):
        return self.filter(role=WS_ADMIN)

    def all_members(self):
        return self.filter(role=WS_MEMBER)


class ActiveMemberManager(models.Manager):
    def get_queryset(self):
        return MemberQuerySet(self.model, using=self._db)

    def admins(self):
        return self.get_queryset().admins()

    def members(self):
        return self.get_queryset().members()


class Membership(BaseAvatarModel):
    """
    Membership holds the relation between
    - workspace vs user
    - project vs user

    README: We don't choose to work with Django generic relations for now

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
    name = models.CharField("Name", blank=True, max_length=255)
    job_title = models.CharField("Job title", blank=True, max_length=255)

    objects = models.Manager()
    members = ActiveMemberManager()

    @property
    def workspace(self):
        if self.object_type == MSP_WORKSPACE:
            return Workspace.objects.get(uuid=self.object_uuid)
        return None

    def get_status(self):
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

    def get_name(self):
        """
        Get name, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.name
        return self.name

    def get_job_title(self):
        """
        Get job_title, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.job_title
        return self.job_title

    def get_avatar(self):
        """
        Get avatar, respecting the `use_global_profile` setting
        """
        if self.use_global_profile and self.user:
            return self.user.avatar_cdn_locations
        return self.avatar_cdn_locations

    def to_deleted(self):
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

            # Copy the avatar from the user to membership
            self.write(self.user.avatar_path.open("rb"))

        super().to_deleted()

    class Meta:
        ordering = ["-created_at"]
        unique_together = [["user", "object_uuid", "object_type", "deleted_at"]]


class UserProfile(Membership):
    """For now, the UserProfile extends the Membership model and contains the same information as the Membership."""

    pass


class Invitation(Membership):
    email = models.EmailField(blank=False)

    @property
    def token_signer(self):
        return signing.TimestampSigner()

    def generate_token(self):
        return self.token_signer.sign(self.suuid)
