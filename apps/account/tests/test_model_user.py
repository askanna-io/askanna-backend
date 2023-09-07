from tests.utils import get_avatar_content_file


def test_user_get_user_memberships(test_users, test_memberships):
    user = test_users["askanna_super_admin"]
    assert user.memberships.exists() is False

    user = test_users["workspace_admin"]
    assert user.memberships.exists() is True
    assert user.memberships.filter(object_type="PROJECT").exists() is False


def test_user_set_avatar(test_users):
    user = test_users["workspace_admin"]
    user.set_avatar(get_avatar_content_file())
    avatar_file_suuids = [avatar_file.suuid for avatar_file in user.avatar_files]

    user.set_avatar(get_avatar_content_file())
    assert user.avatar_files.count() == 5
    for avatar_file in user.avatar_files:
        assert avatar_file.suuid not in avatar_file_suuids


def test_user_to_deleted(test_users, test_memberships):
    user = test_users["workspace_admin"]
    user.set_avatar(get_avatar_content_file())
    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is None
        assert membership.get_name() == "workspace admin"
        assert membership.get_avatar_files().count() == 5

    assert user.name == "workspace admin"
    assert user.email.startswith("deleted-") is False
    assert user.avatar_files.count() == 5

    user.to_deleted()

    assert user.name == "deleted user"
    assert user.email.startswith("deleted-") is True
    assert user.avatar_files.count() == 0
    memberships = user.memberships.all()
    for membership in memberships:
        assert membership.deleted_at is not None
        assert membership.get_name() == "workspace admin"
        assert membership.get_avatar_files().count() == 5
