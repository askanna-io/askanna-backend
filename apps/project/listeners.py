from django.db.models.signals import pre_save
from django.dispatch import receiver

from account.models.membership import MSP_WORKSPACE
from project.models import Project


@receiver(pre_save, sender=Project)
def add_created_by_member_to_project(sender, instance: Project, **kwargs):
    """
    On creation of a project, add the member to it who created this. We already have the user, but we lookup the
    membership for it. We know this by workspace.
    """
    if instance.created_by_user and (not instance.created_by_member):
        membership = instance.created_by_user.memberships.filter(
            object_uuid=instance.workspace.uuid,
            object_type=MSP_WORKSPACE,
            deleted_at__isnull=True,
        ).first()
        if membership:
            instance.created_by_member = membership
