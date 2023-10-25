from core.permissions.askanna_roles import AskAnnaAdmin, AskAnnaMember


def test_user_get_user_memberships(test_users, test_memberships):
    user = test_users.get("askanna_super_admin")
    assert user.memberships.exists() is False

    user = test_users.get("workspace_admin")
    assert user.memberships.exists() is True
    assert user.memberships.filter(object_type="PROJECT").exists() is False


def test_user_to_deleted(test_users, test_memberships):
    user = test_users.get("workspace_admin")
    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is None

    assert user.name == "workspace admin"
    assert user.email.startswith("deleted_") is False

    user.to_deleted()

    assert user.name == "deleted user"
    assert user.email.startswith("deleted-") is True
    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is not None


def test_user_get_status(test_users):
    user = test_users.get("workspace_admin")
    assert user.get_status() == "active"

    user.is_active = False
    user.save()
    assert user.get_status() == "blocked"


def test_user_get_user_role(test_users):
    user = test_users.get("workspace_admin")
    assert user.get_user_role() == AskAnnaMember

    user.is_superuser = True
    user.save()
    assert user.get_user_role() == AskAnnaAdmin
