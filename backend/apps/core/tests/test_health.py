from django.test import TestCase, override_settings
from django.urls import reverse
from django.core.cache import cache

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, Favorite, GameType, Tag
from apps.crawlers.models import CrawlerConfig, CrawlerTask
from apps.reviews.models import ReviewRecord


class HealthCheckTests(TestCase):
    def test_health_endpoint_reports_application_status(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["status"], "ok")
        self.assertIn("database", response.json()["data"])


@override_settings(CORE_RATE_LIMIT=1, CORE_RATE_LIMIT_WINDOW=60)
class CoreBoundaryTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="operator")
        self.game_type = GameType.objects.create(name="RPG")
        self.tag = Tag.objects.create(name="签到", level=1)
        self.activity = Activity.objects.create(source_url="https://example.com/a", source_site="official", game_name="测试游戏", game_type=self.game_type, activity_name="签到活动", created_by=self.user)
        ActivityScreenshot.objects.create(activity=self.activity, image="activities/test.png")
        self.activity.tags.add(self.tag)
        login = self.client.post(reverse("auth-login"), {"email": self.user.email, "password": "secret"}, content_type="application/json")
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {login.json()['data']['access_token']}"}

    def test_activity_list_is_rate_limited_with_retry_after_and_request_id(self):
        url = reverse("activities")
        self.assertEqual(self.client.get(url, **self.headers).status_code, 200)
        response = self.client.get(url, **self.headers)
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response["Retry-After"], "60")
        self.assertEqual(response.json()["error"]["code"], "rate_limited")
        self.assertIn("request_id", response.json()["error"])

    def test_invalid_pagination_returns_structured_400(self):
        response = self.client.get(reverse("activities"), {"page": "bad"}, **self.headers)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"]["code"], "invalid_parameter")
        self.assertIn("request_id", response.json()["error"])

    def test_missing_and_archived_resources_use_structured_errors_and_are_hidden(self):
        missing = self.client.get(reverse("activity-detail", args=[99999]), **self.headers)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"]["code"], "not_found")
        self.activity.status = Activity.STATUS_ARCHIVED
        self.activity.save(update_fields=["status"])
        hidden = self.client.get(reverse("activity-detail", args=[self.activity.pk]), **self.headers)
        self.assertEqual(hidden.status_code, 404)
        self.assertEqual(hidden.json()["error"]["code"], "not_found")

    def test_crawler_delete_is_soft_disable_and_task_history_remains(self):
        config = CrawlerConfig.objects.create(source="source", cron="0 0 * * *")
        task = CrawlerTask.objects.create(config=config)
        admin = User.objects.create_user(email="delete-admin@example.com", username="delete-admin", password="secret", role="admin")
        login = self.client.post(reverse("auth-login"), {"email": admin.email, "password": "secret"}, content_type="application/json")
        admin_headers = {"HTTP_AUTHORIZATION": f"Bearer {login.json()['data']['access_token']}"}
        response = self.client.delete(reverse("crawler-config-detail", args=[config.pk]), **admin_headers)
        self.assertEqual(response.status_code, 204)
        config.refresh_from_db()
        self.assertFalse(config.enabled)
        self.assertTrue(CrawlerConfig.objects.filter(pk=config.pk).exists())
        self.assertTrue(CrawlerTask.objects.filter(pk=task.pk).exists())

    def test_archived_activity_is_visible_to_admin_with_include_archived(self):
        self.activity.status = Activity.STATUS_ARCHIVED
        self.activity.save(update_fields=["status"])
        admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        login = self.client.post(reverse("auth-login"), {"email": admin.email, "password": "secret"}, content_type="application/json")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {login.json()['data']['access_token']}"}
        response = self.client.get(reverse("activities"), {"include_archived": "true"}, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["total"], 1)
