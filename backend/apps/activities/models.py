from django.core.exceptions import ValidationError
from django.db import models


class GameType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]


class Tag(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.PROTECT, related_name="children")
    level = models.PositiveSmallIntegerField(default=1)
    description = models.TextField(blank=True)
    ai_hints = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["parent", "name"], name="unique_tag_sibling_name")]
        ordering = ["sort_order", "name"]

    def clean(self):
        if self.level < 1 or self.level > 3:
            raise ValidationError({"level": "标签层级必须在 1 到 3 级之间。"})
        if self.parent_id and self.level != self.parent.level + 1:
            raise ValidationError({"level": "子标签层级必须比父标签高一级。"})
        if not self.parent_id and self.level != 1:
            raise ValidationError({"parent": "非一级标签必须选择父标签。"})


class Activity(models.Model):
    STATUS_PENDING_TAGGING = "pending_tagging"
    STATUS_PENDING_ADMIN_REVIEW = "pending_admin_review"
    STATUS_ACTIVE = "active"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_PENDING_TAGGING, "待打标"),
        (STATUS_PENDING_ADMIN_REVIEW, "待管理员审核"),
        (STATUS_ACTIVE, "正式"),
        (STATUS_ARCHIVED, "已归档"),
    ]

    SOURCE_CHOICES = [
        ("game-ui", "Game UI"),
        ("official", "官方官网"),
        ("community", "官方社区"),
        ("manual", "手动录入"),
    ]

    source_url = models.URLField()
    source_site = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    game_name = models.CharField(max_length=200)
    game_type = models.ForeignKey(GameType, on_delete=models.PROTECT, related_name="activities")
    activity_name = models.CharField(max_length=200)
    activity_start = models.DateField(null=True, blank=True)
    activity_end = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_by = models.ForeignKey("accounts.User", null=True, on_delete=models.PROTECT, related_name="created_activities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="activities")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["source_url", "game_name", "activity_name"], name="unique_activity_source_identity")]
        ordering = ["-created_at"]

    def clean(self):
        errors = {}
        if self.game_type_id and not self.game_type.is_active:
            errors["game_type"] = "停用的游戏类型不能用于新活动。"
        if self.pk and not self.screenshots.exists():
            errors["screenshots"] = "活动至少需要一张截图。"
        if self.pk and not self.tags.exists():
            errors["tags"] = "活动至少需要一个标签。"
        if errors:
            raise ValidationError(errors)


class ActivityScreenshot(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="screenshots")
    image = models.ImageField(upload_to="activities/")
    caption = models.CharField(max_length=200, blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]


class Favorite(models.Model):
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="favorites")
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="favorites")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "activity"], name="unique_user_activity_favorite")]
        ordering = ["-created_at"]
