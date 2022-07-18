# -*- coding: utf-8 -*-
from dateutil.parser import parse as date_parse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .base import BaseJobTestDef


class TestJobRunModel(BaseJobTestDef, APITestCase):
    """
    Test JobRun model functions
    """

    def test_jobrun_function__str__run_with_name(self):
        self.assertEqual(str(self.jobruns["run1"]), f"run1 ({self.jobruns['run1'].short_uuid})")

    def test_jobrun_function__str__run_with_no_name(self):
        self.assertEqual(str(self.jobruns["run7"]), str(self.jobruns["run7"].short_uuid))

    def test_jobrun_function_set_status(self):
        self.assertEqual(self.jobruns["run7"].status, "FAILED")
        modified_before = self.jobruns["run7"].modified

        self.jobruns["run7"].set_status("COMPLETED")
        self.assertEqual(self.jobruns["run7"].status, "COMPLETED")
        self.assertGreater(self.jobruns["run7"].modified, modified_before)

        # Set status of run7 ack to failed
        self.jobruns["run7"].set_status("FAILED")

    def test_jobrun_function_set_finished(self):
        self.assertIsNone(self.jobruns["run6"].finished)
        self.assertIsNone(self.jobruns["run6"].duration)
        modified_before = self.jobruns["run6"].modified

        self.jobruns["run6"].set_finished()
        self.assertIsNotNone(self.jobruns["run6"].finished)
        self.assertIsNotNone(self.jobruns["run6"].duration)
        self.assertGreater(self.jobruns["run6"].finished, self.jobruns["run6"].started)
        self.assertGreater(self.jobruns["run6"].modified, modified_before)

        duration = (self.jobruns["run6"].finished - self.jobruns["run6"].started).seconds
        self.assertEqual(self.jobruns["run6"].duration, duration)


class TestJobRunListAPI(BaseJobTestDef, APITestCase):
    """
    Test to list the Jobruns
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "runinfo-list",
            kwargs={"version": "v1"},
        )

    def test_list_as_admin(self):
        """
        We can list jobruns as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)

    def test_list_as_member(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)

    def test_list_as_nonmember(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_as_anonymous(self):
        """
        We can list jobruns as member of a workspace
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # we should only list run6 as this is in a public project
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0].get("name"), "run6")

    def test_list_as_member_filter_by_job(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        filter_params = {"job": self.jobdef.short_uuid}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        filter_params = {"job": ",".join([self.jobdef.short_uuid, self.jobdef2.short_uuid])}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_by_project(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 5)


class TestJobJobRunListAPI(TestJobRunListAPI):
    """
    Test to list the Jobruns
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-runs-list",
            kwargs={
                "version": "v1",
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )

    def test_list_as_admin(self):
        """
        We can list jobruns as admin of a workspace
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_nonmember(self):
        """
        We can not list jobruns as non-member of a workspace
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_as_anonymous(self):
        """
        Anonymous can only list public runs, so this one returns 0 runs
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_list_as_member_filter_by_job(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        filter_params = {"job": self.jobdef.short_uuid}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_by_jobs(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        filter_params = {"job": ",".join([self.jobdef.short_uuid, self.jobdef2.short_uuid])}
        response = self.client.get(
            self.url,
            filter_params,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_list_as_member_filter_by_project(self):
        """
        We can list jobruns as member of a workspace
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)


class TestJobRunDetailAPI(BaseJobTestDef, APITestCase):

    """
    Test to get details of a Jobrun
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )
        self.url_run2 = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )
        self.url_other_workspace = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run3"].short_uuid},
        )

    def test_detail_as_admin(self):
        """
        We can get details of a jobrun as an admin
        """
        self.activate_user("admin")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)

    def test_detail_as_member(self):
        """
        We can get details of a jobrun as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)

    def test_detail_as_member_other_run(self):
        """
        We can get details of a jobrun as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url_run2,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run2"].short_uuid)
        self.assertEqual(response.data.get("result", {}).get("original_name"), "someresult.txt")
        self.assertEqual(response.data.get("result", {}).get("extension"), "txt")

    def test_detail_as_member_changed_membername(self):
        """
        We can get details of a jobrun as a member
        """
        self.activate_user("member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)
        self.assertEqual(response.data.get("owner").get("name"), "name of member in membership")

        # now change membername to new membername
        self.members.get("member").name = "new membername"
        self.members.get("member").save()

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)
        self.assertEqual(response.data.get("owner").get("name"), "new membername")

        # now change back new membername to membername
        self.members.get("member").name = "membername"
        self.members.get("member").save()

    def test_detail_as_member_workspacemembername_different_in_other_workspace(self):
        """
        We can get details of a jobrun as a member
        """
        self.activate_user("member2")

        # first visit 1st workspace
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)
        self.assertEqual(response.data.get("owner").get("name"), "name of member in membership")

        # then visit 2nd workspace
        response = self.client.get(
            self.url_other_workspace,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run3"].short_uuid)
        self.assertEqual(response.data.get("owner").get("name"), "member")

    def test_detail_as_nonmember(self):
        """
        We can NOT get details of a jobrun as non-member
        """
        self.activate_user("non_member")

        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_detail_as_anonymous(self):
        """
        We can NOT get details of a jobrun as anonymous
        """
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestJobJobRunDetailAPI(TestJobRunDetailAPI):

    """
    Test to get details of a Jobrun
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run1"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )
        self.url_run2 = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run2"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )
        self.url_other_workspace = reverse(
            "job-runs-detail",
            kwargs={
                "version": "v1",
                "short_uuid": self.jobruns["run3"].short_uuid,
                "parent_lookup_jobdef__short_uuid": self.jobdef.short_uuid,
            },
        )

    def test_detail_as_member_workspacemembername_different_in_other_workspace(self):
        """
        This detail page is not applicable when in jobjob detail
        """
        pass


class TestJobRunResultAPI(BaseJobTestDef, APITestCase):
    """
    Test to get result of a Jobrun
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "shortcut-jobrun-result",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )

    def test_retrieve_as_admin(self):
        """
        We can get the result for a jobrun as an admin
        """
        self.activate_user("admin")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_member(self):
        """
        We can get the result for a jobrun as a member
        """
        self.activate_user("member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_as_nonmember(self):
        """
        We can NOT get the result for a jobrun as a non-member
        """
        self.activate_user("non_member")

        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_retrieve_as_anonymous(self):
        """
        We can NOT get the result of a jborun as anonymous
        """
        response = self.client.get(self.url, format="json", HTTP_HOST="testserver")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestJobRunDetailUpdateAPI(BaseJobTestDef, APITestCase):
    """
    Test whether we can change the name and description of the run object
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )
        self.url_run2 = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run2"].short_uuid},
        )
        self.url_other_workspace = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run3"].short_uuid},
        )

    def run_test(self):
        initial_response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(initial_response.status_code, status.HTTP_200_OK)
        self.assertTrue(initial_response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)
        self.assertEqual(initial_response.data.get("name"), self.jobruns["run1"].name)
        self.assertEqual(
            date_parse(initial_response.data.get("modified")),
            self.jobruns["run1"].modified,
        )
        self.assertEqual(initial_response.data.get("description"), self.jobruns["run1"].description)

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("short_uuid") == self.jobruns["run1"].short_uuid)
        self.assertEqual(response.data.get("name"), "new name")
        self.assertEqual(response.data.get("description"), "new description")
        # the modified time of the run can be changed as changing name/description will update the
        # modified field.
        self.assertNotEqual(
            date_parse(response.data.get("modified")),
            self.jobruns["run1"].modified,
        )

    def test_update_as_admin(self):
        """
        We can update name and detail of the run as admin
        """
        self.activate_user("admin")
        self.run_test()

    def test_update_as_member(self):
        """
        We can update name and detail of the run as member
        """
        self.activate_user("member")
        self.run_test()

    def test_update_as_nonmember(self):
        """
        We can NOT update name and detail of the run as non-member
        """
        self.activate_user("non_member")

        response = self.client.patch(
            self.url,
            {
                "name": "new name",
                "description": "new description",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class TestRunDeleteAPI(BaseJobTestDef, APITestCase):
    """
    Test on the deletion of a Run
    """

    def setUp(self):
        super().setUp()
        self.url = reverse(
            "runinfo-detail",
            kwargs={"version": "v1", "short_uuid": self.jobruns["run1"].short_uuid},
        )

    def is_deleted(self):
        # is it deleted?
        response = self.client.get(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_anna(self):
        """
        AskAnna user by default don't have the permission to delete a run
        """
        self.activate_user("anna")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_admin(self):
        """
        We can remove a run as an workspace admin
        """
        self.activate_user("admin")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.is_deleted()

    def test_delete_as_member(self):
        """
        we can remove a run as a member of an workspace
        """
        self.activate_user("member")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.is_deleted()

    def test_delete_as_nonmember(self):
        """
        we cannot remove a run when we are not a member of the workspace
        """
        self.activate_user("non_member")

        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_as_anonymous(self):
        """
        As anonoymous user we cannot remove anything
        """
        response = self.client.delete(
            self.url,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
