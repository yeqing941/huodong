from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from apps.accounts.models import User
from apps.activities.models import Activity, ActivityScreenshot, Favorite, GameType, Tag


class ActivityModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="operator@example.com",
            username="operator",
            password="secret",
            role="operator",
        )
        self.game_type = GameType.objects.create(name="RPG")
        self.tag = Tag.objects.create(name="签到", level=1)

    def test_activity_requires_active_game_type_and_screenshot_and_tag(self):
        activity = Activity(
            source_url="https://example.com/activity",
            source_site="official",
            game_name="测试游戏",
            game_type=self.game_type,
            activity_name="签到活动",
            created_by=self.user,
        )
        activity.save()
        ActivityScreenshot.objects.create(activity=activity, image="activities/test.png", sort_order=1)
        activity.tags.add(self.tag)
        activity.full_clean()

    def test_duplicate_activity_identity_is_rejected(self):
        activity = Activity.objects.create(
            source_url="https://example.com/activity",
            source_site="official",
            game_name="测试游戏",
            game_type=self.game_type,
            activity_name="签到活动",
            created_by=self.user,
        )
        ActivityScreenshot.objects.create(activity=activity, image="activities/test.png", sort_order=1)
        activity.tags.add(self.tag)
        with self.assertRaises(IntegrityError):
            Activity.objects.create(
                source_url=activity.source_url,
                source_site=activity.source_site,
                game_name=activity.game_name,
                game_type=self.game_type,
                activity_name=activity.activity_name,
                created_by=self.user,
            )

    def test_favorite_is_unique_per_user_and_activity(self):
        activity = Activity.objects.create(
            source_url="https://example.com/activity",
            source_site="official",
            game_name="测试游戏",
            game_type=self.game_type,
            activity_name="签到活动",
            created_by=self.user,
        )
        Favorite.objects.create(user=self.user, activity=activity)
        with self.assertRaises(IntegrityError):
            Favorite.objects.create(user=self.user, activity=activity)

    def test_tag_cannot_exceed_three_levels(self):
        parent = Tag.objects.create(name="一级", level=1)
        child = Tag.objects.create(name="二级", level=2, parent=parent)
        third = Tag(name="四级", level=4, parent=child)
        with self.assertRaises(ValidationError):
            third.full_clean()
