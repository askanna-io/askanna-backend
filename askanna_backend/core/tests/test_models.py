from core.models import Setting
from package.models import Package


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


def test_file_base_model_filename(db):
    new_run_result = Package.objects.create(size=0)
    assert (
        new_run_result.filename
        == f"{new_run_result.file_type}_{new_run_result.uuid.hex}.{new_run_result.file_extension}"
    )

    Package.file_extension = ""
    assert new_run_result.filename == f"{new_run_result.file_type}_{new_run_result.uuid.hex}"
