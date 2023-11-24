def get_workspace_membership(user, workspace):
    from account.models import Membership

    return Membership.objects.get_workspace_membership(user, workspace)
