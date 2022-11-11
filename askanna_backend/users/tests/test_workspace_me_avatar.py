"""Define tests for API of updating user profile image."""
import pytest
from django.urls import reverse
from rest_framework.test import APITestCase

from .test_global_me_avatar import BaseTestAvatarAPI
from .test_workspace_me import WorkspaceTestSet

pytestmark = pytest.mark.django_db


class TestWorkspaceAvatarAPI(WorkspaceTestSet, BaseTestAvatarAPI, APITestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse(
            "workspace-me-avatar",
            kwargs={
                "version": "v1",
                "suuid": self.workspace.suuid,
            },
        )

    def test_update_avatar_as_anna(self):
        """
        Skip test for updating avatar as `anna`, since `anna` doesn't have a profile on workspaces
        """
        pass
