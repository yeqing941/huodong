import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import has_permission
from apps.accounts.views import error_response, user_from_request

from .models import CrawlerConfig, CrawlerFailure, CrawlerTask
from .services import create_task, retry_failure


def auth(request, permission="crawler:operate"):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if permission and not has_permission(user, permission):
        return None, error_response(403, "forbidden", "无权执行此操作")
    return user, None


def payload_config(item):
    return {"id": item.pk, "source": item.source, "rule_summary": item.rule_summary, "game_scope": item.game_scope, "cron": item.cron, "enabled": item.enabled, "consecutive_failures": item.consecutive_failures, "auto_paused": item.auto_paused, "last_run_at": item.last_run_at.isoformat() if item.last_run_at else None}


def payload_task(item):
    return {"id": item.pk, "config_id": item.config_id, "status": item.status, "trigger_type": item.trigger_type, "source": item.source, "game_scope": item.game_scope, "discovered_count": item.discovered_count, "new_count": item.new_count, "duplicate_count": item.duplicate_count, "failed_count": item.failed_count, "pending_tagging_count": item.pending_tagging_count, "started_at": item.started_at.isoformat() if item.started_at else None, "finished_at": item.finished_at.isoformat() if item.finished_at else None}


def payload_failure(item):
    return {"id": item.pk, "task_id": item.task_id, "url": item.url, "error_type": item.error_type, "reason": item.reason, "retry_count": item.retry_count, "last_retried_at": item.last_retried_at.isoformat() if item.last_retried_at else None, "status": item.status}


def configs(request, config_id=None):
    user, failure = auth(request)
    if failure:
        return failure
    if config_id:
        item = get_object_or_404(CrawlerConfig, pk=config_id)
        if request.method == "GET":
            return JsonResponse({"data": payload_config(item), "meta": {}})
        if user.role != "admin":
            return error_response(403, "forbidden", "仅管理员可修改爬虫配置")
        if request.method == "PATCH":
            try:
                body = json.loads(request.body or "{}")
                for field in ("source", "rule_summary", "game_scope", "cron", "enabled", "adapter_mode"):
                    if field in body:
                        setattr(item, field, body[field])
                item.save()
                return JsonResponse({"data": payload_config(item), "meta": {}})
            except (json.JSONDecodeError, TypeError):
                return error_response(400, "invalid_config", "配置无效")
        if request.method == "DELETE":
            item.delete()
            return JsonResponse({}, status=204)
        return error_response(405, "method_not_allowed", "请求方法不支持")
    if request.method == "GET":
        items = CrawlerConfig.objects.all()
        if request.GET.get("status") == "enabled":
            items = items.filter(enabled=True)
        return JsonResponse({"data": {"items": [payload_config(x) for x in items], "total": items.count()}, "meta": {}})
    if user.role != "admin":
        return error_response(403, "forbidden", "仅管理员可修改爬虫配置")
    if request.method == "POST":
        try:
            body = json.loads(request.body or "{}")
            item = CrawlerConfig.objects.create(source=body["source"], rule_summary=body.get("rule_summary", ""), game_scope=body.get("game_scope", []), cron=body["cron"], enabled=body.get("enabled", True), adapter_mode=body.get("adapter_mode", "default"))
            return JsonResponse({"data": payload_config(item), "meta": {}}, status=201)
        except (json.JSONDecodeError, KeyError, TypeError):
            return error_response(400, "invalid_config", "配置无效")
    return error_response(405, "method_not_allowed", "请求方法不支持")


def config_state(request, config_id, enabled):
    user, failure = auth(request)
    if failure:
        return failure
    if user.role != "admin":
        return error_response(403, "forbidden", "仅管理员可修改爬虫配置")
    item = get_object_or_404(CrawlerConfig, pk=config_id)
    item.enabled = enabled
    if enabled:
        item.auto_paused = False
        item.consecutive_failures = 0
    item.save(update_fields=["enabled", "auto_paused", "consecutive_failures"])
    return JsonResponse({"data": payload_config(item), "meta": {}})


def tasks(request, task_id=None, retry=False):
    user, failure = auth(request)
    if failure:
        return failure
    if task_id:
        task = get_object_or_404(CrawlerTask, pk=task_id)
        if retry and request.method == "POST":
            for item in task.failures.filter(status__in=[CrawlerFailure.STATUS_PENDING, CrawlerFailure.STATUS_FAILED]):
                retry_failure(item)
            return JsonResponse({"data": payload_task(task), "meta": {}}, status=202)
        if request.method == "GET":
            data = payload_task(task)
            data["failures"] = [payload_failure(item) for item in task.failures.all()]
            return JsonResponse({"data": data, "meta": {}})
        return error_response(405, "method_not_allowed", "请求方法不支持")
    if request.method == "GET":
        items = CrawlerTask.objects.all()
        return JsonResponse({"data": {"items": [payload_task(x) for x in items], "total": items.count()}, "meta": {}})
    if request.method == "POST":
        try:
            body = json.loads(request.body or "{}")
            config = get_object_or_404(CrawlerConfig, pk=body["config_id"])
        except (json.JSONDecodeError, KeyError):
            return error_response(400, "invalid_task", "任务参数无效")
        if not config.enabled or config.auto_paused:
            return error_response(409, "config_disabled", "爬虫配置未启用")
        if CrawlerTask.objects.filter(config=config, status__in=[CrawlerTask.STATUS_QUEUED, CrawlerTask.STATUS_RUNNING, CrawlerTask.STATUS_PARTIAL]).exists():
            return error_response(409, "duplicate_task", "该配置已有任务")
        task = create_task(config)
        return JsonResponse({"data": payload_task(task), "meta": {}}, status=202)
    return error_response(405, "method_not_allowed", "请求方法不支持")


def failures(request, task_id, failure_id=None):
    user, failure = auth(request)
    if failure:
        return failure
    item = get_object_or_404(CrawlerFailure, task_id=task_id, pk=failure_id) if failure_id else None
    if item:
        if request.method != "POST":
            return error_response(405, "method_not_allowed", "请求方法不支持")
        return JsonResponse({"data": payload_failure(retry_failure(item)), "meta": {}}, status=202)
    task = get_object_or_404(CrawlerTask, pk=task_id)
    items = task.failures.all()
    return JsonResponse({"data": {"items": [payload_failure(x) for x in items], "total": items.count()}, "meta": {}})
