import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.dateparse import parse_datetime

from apps.accounts.views import error_response, user_from_request
from .models import AuditLog


def _admin(request):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if user.role != "admin":
        return None, error_response(403, "forbidden", "仅管理员可查看审计日志")
    return user, None


def _payload(item):
    return {
        "id": str(item.pk), "actor_id": str(item.actor_id) if item.actor_id else None,
        "actor_email": item.actor.email if item.actor else None, "action": item.action,
        "object_type": item.object_type, "object_id": item.object_id, "success": item.success,
        "before_data": item.before_data, "after_data": item.after_data, "note": item.note,
        "created_at": item.created_at.isoformat(),
    }


def audit_logs(request):
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "GET":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    items = AuditLog.objects.select_related("actor").all()
    for field in ("action", "object_type", "object_id"):
        if request.GET.get(field):
            items = items.filter(**{field: request.GET[field]})
    if request.GET.get("actor_id"):
        items = items.filter(actor_id=request.GET["actor_id"])
    if request.GET.get("success") in {"true", "false"}:
        items = items.filter(success=request.GET["success"] == "true")
    if request.GET.get("start_time"):
        items = items.filter(created_at__gte=parse_datetime(request.GET["start_time"]))
    if request.GET.get("end_time"):
        items = items.filter(created_at__lte=parse_datetime(request.GET["end_time"]))
    paginator = Paginator(items, min(int(request.GET.get("page_size", 50)), 100))
    page = paginator.get_page(request.GET.get("page", 1))
    return JsonResponse({"data": {"items": [_payload(item) for item in page.object_list], "total": paginator.count, "page": page.number, "page_size": paginator.per_page}, "meta": {}})
