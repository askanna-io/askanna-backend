from core.permissions.roles import AskAnnaAdmin, AskAnnaMember


def test_user_get_user_memberships(test_users, test_memberships):
    user = test_users["askanna_super_admin"]
    assert user.memberships.exists() is False

    user = test_users["workspace_admin"]
    assert user.memberships.exists() is True
    assert user.memberships.filter(object_type="PROJECT").exists() is False


def test_user_set_avatar(test_users, avatar_content_file):
    user = test_users["workspace_admin"]
    user.set_avatar(avatar_content_file)
    avatar_file_suuid = user.avatar_file.suuid

    user.set_avatar(avatar_content_file)
    assert user.avatar_file is not None
    assert user.avatar_file.suuid != avatar_file_suuid


def test_user_to_deleted(test_users, test_memberships, avatar_content_file):
    user = test_users["workspace_admin"]
    user.set_avatar(avatar_content_file)
    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is None
        assert membership.get_name() == "workspace admin"
        assert membership.get_avatar_file() is not None

    assert user.name == "workspace admin"
    assert user.email.startswith("deleted-") is False
    assert user.avatar_file is not None

    user.to_deleted()

    assert user.name == "deleted user"
    assert user.email.startswith("deleted-") is True
    assert user.avatar_file is None

    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is not None
        assert membership.get_name() == "workspace admin"
        assert membership.get_avatar_file() is not None

        membership.delete_avatar_file()


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
