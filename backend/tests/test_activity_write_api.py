import csv
import io
import json
from datetime import date

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, GameType, Tag


PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82"
)


@override_settings(MEDIA_ROOT="test-media")
class ActivityWriteApiTask6Tests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.other_operator = User.objects.create_user(email="other@example.com", username="other", password="secret", role="operator")
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.game_type = GameType.objects.create(name="RPG")
        self.other_game_type = GameType.objects.create(name="SLG")
        self.tag = Tag.objects.create(name="签到", level=1)
        self.other_tag = Tag.objects.create(name="抽奖", level=1)

    def auth(self, user):
        response = self.client.post(reverse("auth-login"), {"email": user.email, "password": "secret"}, content_type="application/json")
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['data']['access_token']}"}

    def image(self, name="screen.png", content_type="image/png"):
        return SimpleUploadedFile(name, PNG_BYTES, content_type=content_type)

    def make_activity(self, owner=None, name="旧活动"):
        activity = Activity.objects.create(
            source_url=f"https://example.com/{name}",
            source_site="manual",
            game_name="旧游戏",
            game_type=self.game_type,
            activity_name=name,
            created_by=owner or self.operator,
        )
        activity.tags.add(self.tag)
        ActivityScreenshot.objects.create(activity=activity, image=self.image(f"{name}.png"))
        return activity

    def test_operator_can_edit_own_activity(self):
        activity = self.make_activity(self.operator)
        response = self.client.patch(
            reverse("activity-detail", args=[activity.pk]),
            data=json.dumps({
                "activity_name": "更新活动",
                "game_name": "更新游戏",
                "activity_start": "2026-11-01",
                "activity_end": "2026-11-30",
                "tag_ids": [self.other_tag.pk],
            }),
            content_type="application/json",
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 200)
        activity.refresh_from_db()
        self.assertEqual(activity.activity_name, "更新活动")
        self.assertEqual(activity.activity_start, date(2026, 11, 1))
        self.assertEqual(list(activity.tags.values_list("pk", flat=True)), [self.other_tag.pk])

    def test_operator_cannot_edit_another_operators_activity(self):
        activity = self.make_activity(self.other_operator)
        response = self.client.patch(
            reverse("activity-detail", args=[activity.pk]),
            data=json.dumps({"activity_name": "越权修改"}),
            content_type="application/json",
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 403)

    def test_admin_can_edit_any_activity(self):
        activity = self.make_activity(self.other_operator)
        response = self.client.patch(
            reverse("activity-detail", args=[activity.pk]),
            data=json.dumps({"activity_name": "管理员修改", "game_type_id": self.other_game_type.pk}),
            content_type="application/json",
            **self.auth(self.admin),
        )
        self.assertEqual(response.status_code, 200)
        activity.refresh_from_db()
        self.assertEqual(activity.activity_name, "管理员修改")
        self.assertEqual(activity.game_type_id, self.other_game_type.pk)

    def test_regular_user_cannot_edit_activity(self):
        activity = self.make_activity(self.operator)
        response = self.client.patch(
            reverse("activity-detail", args=[activity.pk]),
            data=json.dumps({"activity_name": "普通用户修改"}),
            content_type="application/json",
            **self.auth(self.user),
        )
        self.assertEqual(response.status_code, 403)

    def test_multipart_screenshot_is_persisted_without_removing_existing(self):
        activity = self.make_activity(self.operator)
        response = self.client.post(
            reverse("activity-screenshots", args=[activity.pk]),
            data={"image": self.image(), "caption": "新截图", "sort_order": "2"},
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(ActivityScreenshot.objects.filter(activity=activity).count(), 2)
        screenshot = ActivityScreenshot.objects.get(activity=activity, caption="新截图")
        self.assertTrue(screenshot.image.name.startswith("activities/"))
        self.assertIn("/media/activities/", response.json()["data"]["url"])

    def test_invalid_screenshot_is_rejected(self):
        activity = self.make_activity(self.operator)
        response = self.client.post(
            reverse("activity-screenshots", args=[activity.pk]),
            data={"image": SimpleUploadedFile("bad.txt", b"not-an-image", content_type="text/plain")},
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(ActivityScreenshot.objects.filter(activity=activity).count(), 1)

    def test_csv_import_persists_valid_rows_and_queryable_issues(self):
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["activity_name", "game_name", "game_type", "source_url", "source_site", "tag"])
        writer.writeheader()
        writer.writerow({"activity_name": "有效活动", "game_name": "有效游戏", "game_type": "RPG", "source_url": "https://example.com/valid", "source_site": "manual", "tag": "签到"})
        writer.writerow({"activity_name": "", "game_name": "缺名游戏", "game_type": "RPG", "source_url": "https://example.com/missing", "source_site": "manual", "tag": "签到"})
        writer.writerow({"activity_name": "坏标签活动", "game_name": "有效游戏", "game_type": "RPG", "source_url": "https://example.com/tag", "source_site": "manual", "tag": "不存在"})
        writer.writerow({"activity_name": "停用类型活动", "game_name": "有效游戏", "game_type": "停用", "source_url": "https://example.com/inactive", "source_site": "manual", "tag": "签到"})
        disabled = GameType.objects.create(name="停用", is_active=False)
        upload = SimpleUploadedFile("activities.csv", output.getvalue().encode("utf-8-sig"), content_type="text/csv")

        response = self.client.post(reverse("activity-import"), data={"file": upload}, **self.auth(self.operator))
        self.assertEqual(response.status_code, 201)
        result = response.json()["data"]
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["valid_count"], 1)
        self.assertEqual(result["issue_count"], 3)
        self.assertTrue(Activity.objects.filter(activity_name="有效活动").exists())
        self.assertEqual(result["issues"][0]["row"], 3)
        self.assertIn("活动名称", result["issues"][0]["message"])
        self.assertEqual(disabled.name, "停用")

        queried = self.client.get(reverse("activity-import-detail", args=[result["id"]]), **self.auth(self.operator))
        self.assertEqual(queried.status_code, 200)
        self.assertEqual(queried.json()["data"]["issue_count"], 3)
