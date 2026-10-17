from django.db import models


class CrawlerConfig(models.Model):
    source = models.CharField(max_length=100)
    rule_summary = models.TextField(blank=True)
    game_scope = models.JSONField(default=list)
    cron = models.CharField(max_length=100)
    enabled = models.BooleanField(default=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    auto_paused = models.BooleanField(default=False)
    adapter_mode = models.CharField(max_length=30, default="default")
    last_run_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]


class CrawlerTask(models.Model):
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_PARTIAL = "partial"
    STATUS_FAILED = "failed"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [(item, item) for item in (STATUS_QUEUED, STATUS_RUNNING, STATUS_COMPLETED, STATUS_PARTIAL, STATUS_FAILED, STATUS_CANCELLED)]

    config = models.ForeignKey(CrawlerConfig, on_delete=models.PROTECT, related_name="tasks")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    trigger_type = models.CharField(max_length=20, default="manual")
    source = models.CharField(max_length=100, blank=True)
    game_scope = models.JSONField(default=list)
    discovered_count = models.PositiveIntegerField(default=0)
    new_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    pending_tagging_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class CrawlerFailure(models.Model):
    STATUS_PENDING = "pending"
    STATUS_RETRYING = "retrying"
    STATUS_RESOLVED = "resolved"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [(item, item) for item in (STATUS_PENDING, STATUS_RETRYING, STATUS_RESOLVED, STATUS_FAILED)]

    task = models.ForeignKey(CrawlerTask, on_delete=models.CASCADE, related_name="failures")
    url = models.URLField()
    error_type = models.CharField(max_length=100)
    reason = models.TextField()
    retry_count = models.PositiveIntegerField(default=0)
    last_retried_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
