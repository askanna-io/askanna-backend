import unittest

from core.container import get_descriptive_docker_error


class TestContainerMessage(unittest.TestCase):
    def test_descriptive_errors(self):
        self.assertEqual(
            get_descriptive_docker_error("Image was not found"),
            "The image was not found, please check your askanna.yml whether the environment image is correct.",
        )
        self.assertEqual(
            get_descriptive_docker_error("unauthorized access"),
            "We could not authenticate you to the registry. Please check the environment username and password.",
        )
