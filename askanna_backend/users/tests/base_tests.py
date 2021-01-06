from users.models import User


class BaseUsers:
    @classmethod
    def setup_class(cls):
        cls.users = {
            "admin": User.objects.create_superuser(
                username="admin2",
                is_staff=True,
                is_superuser=True,
                email="admin2@askanna.dev",
                password="password-admin",
            ),
            "user": User.objects.create_user(
                username="user", email="user@askanna.dev", password="password-user"
            ),
            "userB": User.objects.create(
                username="userB", email="userB@askanna.dev", password="password-userB"
            ),
        }

    @classmethod
    def teardown_class(cls):
        """
        Remove all the user instances we had setup for the test
        """
        for _, user in cls.users.items():
            user.delete()
