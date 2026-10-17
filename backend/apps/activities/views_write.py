import csv
import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from apps.accounts.permissions import has_permission
from apps.accounts.views import error_response, user_from_request

from .importers import import_activity_csv
from .models import Activity, ActivityImport
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


def activity_import(request):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    if not has_permission(user, "activity:write"):
        return error_response(403, "forbidden", "无权导入活动")
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    upload = request.FILES.get("file")
    if not upload or not upload.name.lower().endswith(".csv"):
        return error_response(400, "invalid_import", "必须上传 CSV 文件")
    try:
        result = import_activity_csv(upload, user)
    except (UnicodeDecodeError, csv.Error, ValueError):
        return error_response(400, "invalid_import", "CSV 文件格式无效")
    return JsonResponse({"data": import_payload(result), "meta": {}}, status=201)


def import_payload(result):
    return {
        "id": str(result.pk),
        "filename": result.filename,
        "status": result.status,
        "valid_count": result.valid_count,
        "issue_count": result.issue_count,
        "issues": result.issues,
        "created_at": result.created_at.isoformat(),
    }


def activity_import_detail(request, import_id):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    result = get_object_or_404(ActivityImport, pk=import_id)
    if result.created_by_id != user.pk and user.role != "admin":
        return error_response(403, "forbidden", "无权查看此导入结果")
    return JsonResponse({"data": import_payload(result), "meta": {}})
