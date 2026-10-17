from django.contrib.auth import get_user_model
from django.test import TestCase


class UserModelTests(TestCase):
    def test_user_password_is_hashed_and_disabled_user_is_not_active(self):
        user = get_user_model().objects.create_user(
            email="operator@example.com",
            username="operator",
            password="secret",
            role="operator",
        )

        self.assertNotEqual(user.password, "secret")
        self.assertTrue(user.check_password("secret"))
        user.status = "disabled"
        user.save(update_fields=["status"])
        self.assertFalse(user.is_active)
