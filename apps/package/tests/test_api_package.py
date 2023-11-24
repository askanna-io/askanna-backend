import pytest
from django.urls import reverse
from rest_framework import status

from tests import AskAnnaAPITestCase


class TestPackageBase(AskAnnaAPITestCase):
    @pytest.fixture(autouse=True)
    def _set_fixtures(self, test_users, test_projects, test_packages, test_memberships, test_storage_files):
        self.users = test_users
        self.projects = test_projects
        self.packages = test_packages


class TestPackageDetail(TestPackageBase):
    def test_package_detail(self):
        """
        Test if package detail work and confirm it only work for project admins, members and viewers
        """

        def package_detail_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.get(
                reverse(
                    "package-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": self.packages["package_private_1"].suuid,
                    },
                )
            )

            if expected_status_code != status.HTTP_200_OK:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_200_OK

            assert response.data["suuid"] == self.packages["package_private_1"].suuid
            assert response.data.get("filename") == self.packages["package_private_1"].package_file.name
            assert response.data.get("size") == self.packages["package_private_1"].package_file.size

            assert any("askanna.yml" in file["name"] for file in response.data["files"])

            return True

        assert package_detail_test(user_name="workspace_admin", expected_status_code=status.HTTP_200_OK)
        assert package_detail_test(user_name="workspace_member", expected_status_code=status.HTTP_200_OK)
        assert package_detail_test(user_name="workspace_viewer", expected_status_code=status.HTTP_200_OK)

        assert package_detail_test(user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_detail_test(user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_detail_test(user_name=None, expected_status_code=status.HTTP_404_NOT_FOUND)


class TestPackageList(TestPackageBase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_admin(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_member(self):
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_viewer(self):
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 3

    def test_list_as_non_member(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_anonymous(self):
        """
        Anonymous can only list packages from public projects
        """
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_order_by_created_by_name(self):
        self.set_authorization(self.users["workspace_admin"])

        response_asc = self.client.get(self.url, {"order_by": "created_by.name"})
        assert response_asc.status_code == status.HTTP_200_OK
        assert len(response_asc.data["results"]) == 3

        response_desc = self.client.get(self.url, {"order_by": "-created_by.name"})
        assert response_desc.status_code == status.HTTP_200_OK
        assert len(response_desc.data["results"]) == 3

        assert response_asc.data["results"][-1] != response_desc.data["results"][-1]


class TestProjectPackageList(TestPackageBase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_admin(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_member(self):
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_viewer(self):
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 2

    def test_list_as_non_member(self):
        self.set_authorization(self.users["no_workspace_member"])
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0

    def test_list_as_anonymous(self):
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_private"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 0


class TestPublicProjectPackageList(TestPackageBase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "package-list",
            kwargs={
                "version": "v1",
            },
        )

    def test_list_as_askanna_admin(self):
        self.set_authorization(self.users["askanna_super_admin"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_admin(self):
        self.set_authorization(self.users["workspace_admin"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_member(self):
        self.set_authorization(self.users["workspace_member"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_viewer(self):
        self.set_authorization(self.users["workspace_viewer"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_non_member(self):
        self.set_authorization(self.users["no_workspace_member"])

        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list_as_anonymous(self):
        response = self.client.get(
            self.url,
            {
                "project_suuid": self.projects["project_public"].suuid,
            },
            format="json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1


class TestPackageUpdate(TestPackageBase):
    def test_package_update(self):
        """
        Test if package update work and confirm it only work for project admins and members
        """

        def package_update_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.patch(
                reverse(
                    "package-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": self.packages["package_private_1"].suuid,
                    },
                ),
                {"description": "a new description"},
            )

            if expected_status_code != status.HTTP_200_OK:
                assert response.status_code == expected_status_code
                return True

            assert response.status_code == status.HTTP_200_OK

            assert response.data["suuid"] == self.packages["package_private_1"].suuid
            assert response.data.get("filename") == self.packages["package_private_1"].package_file.name
            assert response.data.get("size") == self.packages["package_private_1"].package_file.size

            assert response.data.get("description") != self.packages["package_private_1"].package_file.description
            assert self.packages["package_private_1"].package_file.description != "a new description"
            assert response.data.get("description") == "a new description"

            return True

        assert package_update_test(user_name="workspace_admin", expected_status_code=status.HTTP_200_OK)
        assert package_update_test(user_name="workspace_member", expected_status_code=status.HTTP_200_OK)

        assert package_update_test(user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_update_test(user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_update_test(user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_update_test(user_name=None, expected_status_code=status.HTTP_404_NOT_FOUND)


class TestPackageDelete(TestPackageBase):
    def test_package_delete(self):
        """
        Test if package delete work and confirm it only work for project admins
        """

        def package_delete_test(user_name: str | None, expected_status_code: int) -> bool:
            self.set_authorization(self.users[user_name]) if user_name else self.client.credentials()

            response = self.client.delete(
                reverse(
                    "package-detail",
                    kwargs={
                        "version": "v1",
                        "suuid": self.packages["package_private_1"].suuid,
                    },
                )
            )

            assert response.status_code == expected_status_code
            return True

        assert package_delete_test(user_name="workspace_admin", expected_status_code=status.HTTP_204_NO_CONTENT)

        assert package_delete_test(user_name="workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_delete_test(user_name="workspace_viewer", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_delete_test(user_name="askanna_super_admin", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_delete_test(user_name="no_workspace_member", expected_status_code=status.HTTP_404_NOT_FOUND)
        assert package_delete_test(user_name=None, expected_status_code=status.HTTP_404_NOT_FOUND)
