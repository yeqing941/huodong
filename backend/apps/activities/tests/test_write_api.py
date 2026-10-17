import json

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, GameType, Tag


class ActivityWriteApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.game_type = GameType.objects.create(name="RPG")
        self.tag = Tag.objects.create(name="签到", level=1)

    def auth(self, user):
        response = self.client.post(reverse("auth-login"), {"email": user.email, "password": "secret"}, content_type="application/json")
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['data']['access_token']}"}

    def payload(self):
        return {
            "source_url": "https://example.com/new",
            "source_site": "manual",
            "game_name": "新游戏",
            "game_type_id": self.game_type.pk,
            "activity_name": "新活动",
            "description": "活动说明",
            "tag_ids": [self.tag.pk],
            "screenshot": "activities/new.png",
        }

    def test_operator_can_create_activity_with_tag_and_screenshot(self):
        response = self.client.post(reverse("activities"), data=json.dumps(self.payload()), content_type="application/json", **self.auth(self.operator))
        self.assertEqual(response.status_code, 201)
        activity = Activity.objects.get(activity_name="新活动")
        self.assertEqual(activity.status, Activity.STATUS_ACTIVE)
        self.assertEqual(activity.tags.count(), 1)
        self.assertEqual(activity.screenshots.count(), 1)

    def test_regular_user_cannot_create_activity(self):
        response = self.client.post(reverse("activities"), data=json.dumps(self.payload()), content_type="application/json", **self.auth(self.user))
        self.assertEqual(response.status_code, 403)

    def test_created_activity_can_be_loaded_by_detail_api(self):
        response = self.client.post(
            reverse("activities"),
            data=json.dumps(self.payload()),
            content_type="application/json",
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 201)
        activity_id = response.json()["data"]["id"]

        detail = self.client.get(
            reverse("activity-detail", args=[activity_id]),
            **self.auth(self.user),
        )

        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["data"]["activity_name"], "新活动")
        self.assertEqual(detail.json()["data"]["game_name"], "新游戏")
        self.assertEqual(detail.json()["data"]["tags"][0]["name"], "签到")
        self.assertEqual(detail.json()["data"]["screenshots"][0]["url"], "/media/activities/new.png")

    def test_admin_can_archive_and_restore_activity(self):
        activity = Activity.objects.create(
            source_url="https://example.com/archive",
            source_site="manual",
            game_name="归档游戏",
            game_type=self.game_type,
            activity_name="归档活动",
            created_by=self.operator,
        )
        ActivityScreenshot.objects.create(activity=activity, image="activities/archive.png")
        activity.tags.add(self.tag)
        archive = self.client.post(reverse("activity-archive", args=[activity.pk]), data=json.dumps({"reason": "测试归档"}), content_type="application/json", **self.auth(self.admin))
        self.assertEqual(archive.status_code, 200)
        activity.refresh_from_db()
        self.assertEqual(activity.status, Activity.STATUS_ARCHIVED)
        restore = self.client.post(reverse("activity-restore", args=[activity.pk]), **self.auth(self.admin))
        self.assertEqual(restore.status_code, 200)
        activity.refresh_from_db()
        self.assertEqual(activity.status, Activity.STATUS_ACTIVE)
