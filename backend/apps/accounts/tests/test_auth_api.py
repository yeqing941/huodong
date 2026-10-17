from django.test import Client, TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com",
            username="user",
            password="secret",
            role="user",
        )
        self.operator = User.objects.create_user(
            email="operator@example.com",
            username="operator",
            password="secret",
            role="operator",
        )

    def test_real_http_login_does_not_require_csrf_cookie(self):
        response = Client(enforce_csrf_checks=True).post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "secret"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["data"]["access_token"])

    def test_login_returns_bearer_token_and_user(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "secret"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["token_type"], "Bearer")
        self.assertTrue(response.json()["data"]["access_token"])
        self.assertEqual(response.json()["data"]["user"]["role"], "user")

    def test_invalid_password_returns_401_error(self):
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "wrong"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "invalid_credentials")
        self.assertIn("request_id", response.json()["error"])

    def test_disabled_user_cannot_login(self):
        self.user.status = "disabled"
        self.user.save(update_fields=["status"])
        response = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "secret"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_me_requires_and_accepts_bearer_token(self):
        login = self.client.post(
            reverse("auth-login"),
            {"email": "user@example.com", "password": "secret"},
            content_type="application/json",
        )
        token = login.json()["data"]["access_token"]

        unauthenticated = self.client.get(reverse("auth-me"))
        self.assertEqual(unauthenticated.status_code, 401)

        response = self.client.get(reverse("auth-me"), HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["email"], "user@example.com")
