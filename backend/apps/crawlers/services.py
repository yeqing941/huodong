from django.db import transaction
from django.utils import timezone

from apps.activities.models import Activity, GameType

from .models import CrawlerConfig, CrawlerFailure, CrawlerTask


def run_adapter(task):
    config = task.config
    task.status = CrawlerTask.STATUS_RUNNING
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at"])
    if config.adapter_mode == "always_fail":
        CrawlerFailure.objects.create(task=task, url="https://test.invalid/failure", error_type="adapter", reason="测试适配器失败")
        task.discovered_count = 1
        task.failed_count = 1
        task.status = CrawlerTask.STATUS_FAILED
        config.consecutive_failures += 1
        if config.consecutive_failures >= 3:
            config.auto_paused = True
            config.enabled = False
        config.last_run_at = timezone.now()
        config.save(update_fields=["consecutive_failures", "auto_paused", "enabled", "last_run_at"])
    else:
        game_name = (config.game_scope or ["测试游戏"])[0]
        game_type, _ = GameType.objects.get_or_create(name="测试类型")
        source_url = f"https://test.invalid/{config.pk}/new"
        identity = {"source_url": source_url, "game_name": game_name, "activity_name": "测试适配器活动"}
        exists = Activity.objects.filter(**identity).exists()
        if not exists:
            Activity.objects.create(source_site="official", game_type=game_type, status=Activity.STATUS_PENDING_TAGGING, created_by=None, **identity)
        task.discovered_count = 2
        task.new_count = 1
        task.duplicate_count = 1
        task.pending_tagging_count = 1
        task.status = CrawlerTask.STATUS_PARTIAL
        config.consecutive_failures = 0
        config.last_run_at = timezone.now()
        config.save(update_fields=["consecutive_failures", "last_run_at"])
    task.finished_at = timezone.now()
    task.save(update_fields=["discovered_count", "new_count", "duplicate_count", "failed_count", "pending_tagging_count", "status", "finished_at"])
    return task


def create_task(config, trigger_type="manual"):
    with transaction.atomic():
        task = CrawlerTask.objects.create(config=config, source=config.source, game_scope=config.game_scope or [], trigger_type=trigger_type)
        return run_adapter(task)


def retry_failure(failure):
    failure.retry_count += 1
    failure.last_retried_at = timezone.now()
    failure.status = CrawlerFailure.STATUS_RESOLVED
    failure.save(update_fields=["retry_count", "last_retried_at", "status"])
    task = failure.task
    task.failed_count = max(task.failed_count - 1, 0)
    if task.failed_count == 0:
        task.status = CrawlerTask.STATUS_COMPLETED
    task.save(update_fields=["failed_count", "status"])
    return failure
