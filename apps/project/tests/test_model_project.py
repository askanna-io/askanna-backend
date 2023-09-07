from project.models import Project


def test_project_active(test_projects):
    assert Project.objects.active().count() == 2  # type: ignore
    test_projects["project_private"].to_deleted()
    assert Project.objects.active().count() == 1  # type: ignore


def test_project_inactive(test_projects):
    assert Project.objects.inactive().count() == 0  # type: ignore
    test_projects["project_private"].to_deleted()
    assert Project.objects.inactive().count() == 1  # type: ignore


def test_project_visibility_private(test_projects):
    project = test_projects["project_private"]
    assert project.visibility == "PRIVATE"
    assert project.is_private is True
    assert project.is_public is False


def test_project_visibility_public(test_projects):
    project = test_projects["project_public"]
    assert project.visibility == "PUBLIC"
    assert project.is_private is False
    assert project.is_public is True
