import json

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, GameType, Tag
from apps.reviews.models import ReviewRecord


class ReviewApiTests(TestCase):
    def setUp(self):
        self.operator = User.objects.create_user(email="operator@example.com", username="operator", password="secret", role="operator")
        self.admin = User.objects.create_user(email="admin@example.com", username="admin", password="secret", role="admin")
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.game_type = GameType.objects.create(name="RPG")
        self.tag = Tag.objects.create(name="签到", level=1)
        self.tag2 = Tag.objects.create(name="福利", level=1)
        self.activity = Activity.objects.create(
            source_url="https://example.com/review",
            source_site="manual",
            game_name="测试游戏",
            game_type=self.game_type,
            activity_name="测试活动",
            created_by=self.operator,
            status=Activity.STATUS_PENDING_TAGGING,
        )
        ActivityScreenshot.objects.create(activity=self.activity, image="activities/review.png")

    def auth(self, user):
        response = self.client.post(reverse("auth-login"), {"email": user.email, "password": "secret"}, content_type="application/json")
        return {"HTTP_AUTHORIZATION": f"Bearer {response.json()['data']['access_token']}"}

    def create_review(self, user=None):
        response = self.client.post(reverse("reviews"), json.dumps({"activity_id": self.activity.pk}), content_type="application/json", **self.auth(user or self.operator))
        self.assertEqual(response.status_code, 201)
        return response.json()["data"]["id"]

    def test_ai_failure_is_persisted_without_losing_original_data(self):
        review_id = self.create_review()
        response = self.client.post(reverse("review-ai-tag", args=[review_id]), json.dumps({"force_failure": True}), content_type="application/json", **self.auth(self.operator))
        self.assertEqual(response.status_code, 200)
        review = ReviewRecord.objects.get(pk=review_id)
        self.assertEqual(review.status, ReviewRecord.STATUS_PENDING_TAGGING)
        self.assertTrue(review.ai_error)
        self.assertEqual(review.original_data["activity_name"], "测试活动")

    def test_operator_submits_candidates_and_admin_approves_activity(self):
        review_id = self.create_review()
        self.client.post(reverse("review-ai-tag", args=[review_id]), content_type="application/json", **self.auth(self.operator))
        response = self.client.post(
            reverse("review-operator", args=[review_id]),
            json.dumps({"action": "submit", "tag_ids": [self.tag.pk, self.tag2.pk]}),
            content_type="application/json",
            **self.auth(self.operator),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ReviewRecord.objects.get(pk=review_id).status, ReviewRecord.STATUS_PENDING_ADMIN_REVIEW)
        response = self.client.post(reverse("review-admin", args=[review_id]), json.dumps({"action": "approve"}), content_type="application/json", **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.status, Activity.STATUS_ACTIVE)
        self.assertEqual(set(self.activity.tags.values_list("pk", flat=True)), {self.tag.pk, self.tag2.pk})
        self.assertEqual(ReviewRecord.objects.get(pk=review_id).status, ReviewRecord.STATUS_APPROVED)

    def test_regular_user_cannot_operate_review_and_operator_cannot_admin_confirm(self):
        review_id = self.create_review()
        self.assertEqual(self.client.post(reverse("review-ai-tag", args=[review_id]), **self.auth(self.user)).status_code, 403)
        self.client.post(reverse("review-ai-tag", args=[review_id]), content_type="application/json", **self.auth(self.operator))
        self.client.post(reverse("review-operator", args=[review_id]), json.dumps({"action": "submit", "tag_ids": [self.tag.pk]}), content_type="application/json", **self.auth(self.operator))
        self.assertEqual(self.client.post(reverse("review-admin", args=[review_id]), json.dumps({"action": "approve"}), content_type="application/json", **self.auth(self.operator)).status_code, 403)

    def test_illegal_state_transition_returns_409_and_return_keeps_activity_data(self):
        review_id = self.create_review()
        self.assertEqual(self.client.post(reverse("review-admin", args=[review_id]), json.dumps({"action": "approve"}), content_type="application/json", **self.auth(self.admin)).status_code, 409)
        original = self.activity.activity_name
        self.client.post(reverse("review-ai-tag", args=[review_id]), content_type="application/json", **self.auth(self.operator))
        self.client.post(reverse("review-operator", args=[review_id]), json.dumps({"action": "submit", "tag_ids": [self.tag.pk]}), content_type="application/json", **self.auth(self.operator))
        response = self.client.post(reverse("review-admin", args=[review_id]), json.dumps({"action": "return", "reason": "需要补充"}), content_type="application/json", **self.auth(self.admin))
        self.assertEqual(response.status_code, 200)
        self.activity.refresh_from_db()
        self.assertEqual(self.activity.activity_name, original)
        self.assertEqual(ReviewRecord.objects.get(pk=review_id).status, ReviewRecord.STATUS_RETURNED)
