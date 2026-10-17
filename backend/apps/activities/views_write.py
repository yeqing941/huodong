import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.permissions import has_permission
from apps.accounts.views import error_response, user_from_request

from .models import Activity
from .views import activity_payload


def archive_activity(request, activity_id):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    if not has_permission(user, "*"):
        return error_response(403, "forbidden", "仅超级管理员可归档活动")
    activity = get_object_or_404(Activity, pk=activity_id)
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        body = {}
    if not body.get("reason"):
        return error_response(400, "archive_reason_required", "归档必须填写原因")
    activity.status = Activity.STATUS_ARCHIVED
    activity.archived_at = timezone.now()
    activity.save(update_fields=["status", "archived_at", "updated_at"])
    return JsonResponse({"data": activity_payload(activity, request), "meta": {}})


def restore_activity(request, activity_id):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    if not has_permission(user, "*"):
        return error_response(403, "forbidden", "仅超级管理员可恢复活动")
    activity = get_object_or_404(Activity, pk=activity_id)
    activity.status = Activity.STATUS_ACTIVE
    activity.archived_at = None
    activity.save(update_fields=["status", "archived_at", "updated_at"])
    return JsonResponse({"data": activity_payload(activity, request), "meta": {}})
