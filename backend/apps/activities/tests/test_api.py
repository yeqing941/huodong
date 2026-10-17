from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, Favorite, GameType, Tag


class ActivityApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="user@example.com", username="user", password="secret", role="user")
        self.game_type = GameType.objects.create(name="RPG")
        self.tag = Tag.objects.create(name="签到", level=1)
        self.activity = Activity.objects.create(
            source_url="https://example.com/a",
            source_site="official",
            game_name="测试游戏",
            game_type=self.game_type,
            activity_name="签到活动",
            created_by=self.user,
        )
        ActivityScreenshot.objects.create(activity=self.activity, image="activities/test.png", sort_order=1)
        self.activity.tags.add(self.tag)
        login = self.client.post(reverse("auth-login"), {"email": self.user.email, "password": "secret"}, content_type="application/json")
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {login.json()['data']['access_token']}"}

    def test_activity_list_filters_by_game_name_and_returns_screenshot(self):
        response = self.client.get(reverse("activities"), {"game_name": "测试"}, **self.headers)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["data"]["total"], 1)
        self.assertEqual(response.json()["data"]["items"][0]["screenshots"][0]["sort_order"], 1)

    def test_activity_detail_and_favorite_flow(self):
        detail = self.client.get(reverse("activity-detail", args=[self.activity.pk]), **self.headers)
        self.assertEqual(detail.status_code, 200)
        self.assertFalse(detail.json()["data"]["is_favorite"])

        favorite = self.client.post(reverse("activity-favorite", args=[self.activity.pk]), **self.headers)
        self.assertEqual(favorite.status_code, 204)
        duplicate = self.client.post(reverse("activity-favorite", args=[self.activity.pk]), **self.headers)
        self.assertEqual(duplicate.status_code, 409)

        listing = self.client.get(reverse("favorites"), **self.headers)
        self.assertEqual(listing.json()["data"]["total"], 1)

        remove = self.client.delete(reverse("activity-favorite", args=[self.activity.pk]), **self.headers)
        self.assertEqual(remove.status_code, 204)
        self.assertFalse(Favorite.objects.filter(user=self.user, activity=self.activity).exists())

    def test_activity_api_requires_login(self):
        response = self.client.get(reverse("activities"))
        self.assertEqual(response.status_code, 401)
