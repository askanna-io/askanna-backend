from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from account.models.membership import MSP_WORKSPACE, Membership
from core.permissions.roles import WorkspaceAdmin
from workspace.models import Workspace


@receiver(post_delete, sender=Workspace)
def remove_memberships_after_workspace_removal(sender, instance, **kwargs):
    """
    Memberships don't have a hard link, so remove manually
    """
    members_in_workspace = Membership.objects.filter(object_type="WS", object_uuid=instance.uuid)
    for member in members_in_workspace:
        member.delete()


@receiver(post_save, sender=Workspace)
def set_memberships_for_workspace_creator(sender, instance: Workspace, created, **kwargs):
    if created:
        if not instance.created_by_user:
            # created_by field will be replaced with a field that store the membership. For now, to prevent creating a
            # workspace without a membership that is not linked to a user, we raise an error here.
            raise ValueError("Workspace must have a creator")

        # Create new membership for this workspace
        membership = Membership.objects.create(
            object_uuid=instance.uuid,
            object_type=MSP_WORKSPACE,
            role=WorkspaceAdmin.code,
            user=instance.created_by_user,
        )

        # Update workspace.member with membership info
        instance.created_by_member = membership
        instance.save(update_fields=["created_by_member"])
