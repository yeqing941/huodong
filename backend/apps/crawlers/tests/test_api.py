import json

from django.test import TestCase

from apps.accounts.models import User
from apps.activities.models import Activity, GameType
from apps.crawlers.models import CrawlerConfig, CrawlerFailure, CrawlerTask


class CrawlerApiTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.config = CrawlerConfig.objects.create(
            source="test-adapter", rule_summary="固定测试规则", game_scope=["测试游戏"], cron="0 0 * * *", enabled=True
        )
        self.config_url = "/api/v1/crawler/configs"
        self.task_url = "/api/v1/crawler/tasks"

    def token(self, user):
        response = self.client.post("/api/v1/auth/login", {"email": user.email, "password": "secret"}, content_type="application/json")
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['data']['access_token']}"}

    def test_admin_can_crud_config_but_operator_and_user_cannot_write(self):
        admin_headers = self.token(self.admin)
        created = self.client.post(self.config_url, data=json.dumps({
            "source": "test-adapter-2", "rule_summary": "规则", "game_scope": ["A"], "cron": "*/5 * * * *", "enabled": True
        }), content_type="application/json", **admin_headers)
        self.assertEqual(created.status_code, 201)
        config_id = created.json()["data"]["id"]
        updated = self.client.patch(f"{self.config_url}/{config_id}", data=json.dumps({"rule_summary": "已更新"}), content_type="application/json", **admin_headers)
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["data"]["rule_summary"], "已更新")
        self.assertEqual(self.client.post(self.config_url, data=json.dumps({}), content_type="application/json", **self.token(self.operator)).status_code, 403)
        self.assertEqual(self.client.patch(f"{self.config_url}/{config_id}", data=json.dumps({"rule_summary": "越权"}), content_type="application/json", **self.token(self.operator)).status_code, 403)
        self.assertEqual(self.client.post(self.config_url, data=json.dumps({}), content_type="application/json", **self.token(self.user)).status_code, 403)
        self.assertEqual(self.client.delete(f"{self.config_url}/{config_id}", **admin_headers).status_code, 204)

    def test_operator_trigger_persists_stats_and_duplicate_trigger_returns_409(self):
        headers = self.token(self.operator)
        response = self.client.post(self.task_url, data=json.dumps({"config_id": self.config.pk}), content_type="application/json", **headers)
        self.assertIn(response.status_code, (200, 202))
        task = CrawlerTask.objects.get(pk=response.json()["data"]["id"])
        self.assertEqual(task.status, CrawlerTask.STATUS_PARTIAL)
        self.assertGreaterEqual(task.discovered_count, 1)
        self.assertEqual(task.new_count, 1)
        self.assertEqual(task.duplicate_count, 1)
        self.assertEqual(task.pending_tagging_count, 1)
        duplicate = self.client.post(self.task_url, data=json.dumps({"config_id": self.config.pk}), content_type="application/json", **headers)
        self.assertEqual(duplicate.status_code, 409)

    def test_user_cannot_trigger_and_failure_retry_is_persisted(self):
        self.assertEqual(self.client.post(self.task_url, data=json.dumps({"config_id": self.config.pk}), content_type="application/json", **self.token(self.user)).status_code, 403)
        task = CrawlerTask.objects.create(config=self.config, status=CrawlerTask.STATUS_PARTIAL, trigger_type="manual")
        failure = CrawlerFailure.objects.create(task=task, url="https://test.invalid/fail", error_type="parse", reason="测试失败")
        retry = self.client.post(f"{self.task_url}/{task.pk}/failures/{failure.pk}/retry", **self.token(self.operator))
        self.assertIn(retry.status_code, (200, 202))
        failure.refresh_from_db()
        self.assertEqual(failure.retry_count, 1)

    def test_three_consecutive_failures_auto_pause_config(self):
        headers = self.token(self.operator)
        self.config.adapter_mode = "always_fail"
        self.config.save(update_fields=["adapter_mode"])
        for _ in range(3):
            response = self.client.post(self.task_url, data=json.dumps({"config_id": self.config.pk}), content_type="application/json", **headers)
            self.assertIn(response.status_code, (200, 202))
        self.config.refresh_from_db()
        self.assertEqual(self.config.consecutive_failures, 3)
        self.assertTrue(self.config.auto_paused)
        self.assertFalse(self.config.enabled)
