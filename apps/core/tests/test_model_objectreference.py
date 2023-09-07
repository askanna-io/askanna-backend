from core.models import ObjectReference


def test_create_object_reference_for_user_object(test_users):
    user = test_users["workspace_admin"]
    object_reference, created = ObjectReference.get_or_create(object=user)

    assert created is True
    assert object_reference.object == user
    assert object_reference.object_type == "account.User"
