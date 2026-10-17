import json

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, GameType, Tag


class TaxonomyApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.root = Tag.objects.create(name="玩法", level=1)
        self.game_type = GameType.objects.create(name="RPG")

    def auth(self, user):
        response = self.client.post(reverse("auth-login"), {"email": user.email, "password": "secret"}, content_type="application/json")
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['data']['access_token']}"}

    def post_json(self, url, body, user):
        return self.client.post(url, data=json.dumps(body), content_type="application/json", **self.auth(user))

    def test_tag_tree_rejects_fourth_level_and_invalid_parent(self):
        child = Tag.objects.create(name="签到", parent=self.root, level=2)
        response = self.post_json(reverse("taxonomy-tags"), {"name": "每日", "parent_id": child.pk, "level": 4}, self.admin)
        self.assertEqual(response.status_code, 400)
        response = self.post_json(reverse("taxonomy-tags"), {"name": "错误", "parent_id": self.root.pk, "level": 3}, self.admin)
        self.assertEqual(response.status_code, 400)

    def test_admin_can_create_edit_disable_tag_and_migrate_activity_links(self):
        old = Tag.objects.create(name="旧", parent=self.root, level=2)
        new = Tag.objects.create(name="新", parent=self.root, level=2)
        activity = Activity.objects.create(source_url="https://example.com/a", source_site="manual", game_name="G", game_type=self.game_type, activity_name="A", created_by=self.admin)
        ActivityScreenshot.objects.create(activity=activity, image="activities/a.png")
        activity.tags.add(old)
        response = self.post_json(reverse("taxonomy-tag-migrate", args=[old.pk]), {"target_id": new.pk}, self.admin)
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(list(activity.tags.values_list("pk", flat=True)), [new.pk])
        response = self.client.patch(reverse("taxonomy-tag-detail", args=[new.pk]), data=json.dumps({"name": "新标签"}), content_type="application/json", **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        response = self.post_json(reverse("taxonomy-tag-disable", args=[new.pk]), {}, self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Tag.objects.get(pk=new.pk).is_active)

    def test_user_and_operator_cannot_manage_taxonomy(self):
        for user in (self.user, self.operator):
            response = self.post_json(reverse("taxonomy-tags"), {"name": "拒绝"}, user)
            self.assertEqual(response.status_code, 403)

    def test_game_type_disable_keeps_history_and_blocks_new_activity(self):
        activity = Activity.objects.create(source_url="https://example.com/h", source_site="manual", game_name="G", game_type=self.game_type, activity_name="历史", created_by=self.admin)
        response = self.post_json(reverse("taxonomy-game-type-disable", args=[self.game_type.pk]), {}, self.admin)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get(reverse("activities"), **self.auth(self.user)).status_code, 200)
        self.assertIn(str(activity.pk), self.client.get(reverse("activities"), **self.auth(self.user)).content.decode())
        response = self.post_json(reverse("activities"), {"source_url": "https://example.com/new", "game_name": "G", "game_type_id": self.game_type.pk, "activity_name": "新", "tag_ids": [self.root.pk], "screenshot": "activities/new.png"}, self.operator)
        self.assertEqual(response.status_code, 400)

    def test_conflicting_tag_merge_returns_409(self):
        other = Tag.objects.create(name="重复", parent=self.root, level=2)
        target = Tag.objects.create(name="目标", parent=self.root, level=2)
        Tag.objects.create(name="重复", parent=other, level=3)
        Tag.objects.create(name="重复", parent=target, level=3)
        response = self.post_json(reverse("taxonomy-tag-merge", args=[other.pk]), {"target_id": target.pk}, self.admin)
        self.assertEqual(response.status_code, 409)
