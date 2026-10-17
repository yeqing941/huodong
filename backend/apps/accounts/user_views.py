import json

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from apps.audit.services import record_audit
from .models import User
from .serializers import serialize_user
from .views import error_response, user_from_request


def _admin(request):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if user.role != User.ROLE_ADMIN:
        return None, error_response(403, "forbidden", "仅管理员可管理用户")
    return user, None


@csrf_exempt
def users(request):
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method == "GET":
        items = User.objects.order_by("id")
        if request.GET.get("role"):
            items = items.filter(role=request.GET["role"])
        if request.GET.get("status"):
            items = items.filter(status=request.GET["status"])
        paginator = Paginator(items, min(int(request.GET.get("page_size", 50)), 100))
        page = paginator.get_page(request.GET.get("page", 1))
        return JsonResponse({"data": {"items": [serialize_user(item) for item in page.object_list], "total": paginator.count, "page": page.number, "page_size": paginator.per_page}, "meta": {}})
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = json.loads(request.body or "{}")
        user = User.objects.create_user(email=body["email"], username=body.get("username", body["email"].split("@")[0]), password=body.get("password", "temporary-password"), role=body.get("role", User.ROLE_USER))
        record_audit(request.auth_user, "user_create", "user", user.pk, after_data=serialize_user(user))
    except (KeyError, ValueError):
        return error_response(400, "invalid_user", "用户字段无效")
    return JsonResponse({"data": serialize_user(user), "meta": {}}, status=201)


@csrf_exempt
def user_detail(request, user_id):
    actor, failure = _admin(request)
    if failure:
        return failure
    user = get_object_or_404(User, pk=user_id)
    if request.method != "PATCH":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return error_response(400, "invalid_json", "请求体不是有效 JSON")
    before = serialize_user(user)
    for field in ("role", "email", "username"):
        if field in body:
            setattr(user, field, body[field])
    try:
        user.full_clean()
        user.save()
    except ValueError:
        return error_response(400, "invalid_user", "用户字段无效")
    after = serialize_user(user)
    if before["role"] != after["role"]:
        action = "role_update"
    else:
        action = "user_update"
    record_audit(actor, action, "user", user.pk, before_data=before, after_data=after)
    return JsonResponse({"data": after, "meta": {}})


@csrf_exempt
def user_state(request, user_id, enabled):
    actor, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    user = get_object_or_404(User, pk=user_id)
    before = serialize_user(user)
    user.status = User.STATUS_ACTIVE if enabled else User.STATUS_DISABLED
    user.save(update_fields=["status", "is_active"])
    after = serialize_user(user)
    record_audit(actor, "user_enable" if enabled else "user_disable", "user", user.pk, before_data=before, after_data=after)
    return JsonResponse({"data": after, "meta": {}})
