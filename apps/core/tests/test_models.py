from core.models import Setting


def test_base_model_not_uuid(db):
    new_setting = Setting.objects.create(uuid=None)
    assert new_setting.uuid is not None


def test_base_model_to_deleted(db):
    new_setting = Setting.objects.create()
    assert new_setting.deleted_at is None

    new_setting.to_deleted()
    assert new_setting.deleted_at is not None

    new_setting.to_deleted()
    assert new_setting.deleted_at is not None
