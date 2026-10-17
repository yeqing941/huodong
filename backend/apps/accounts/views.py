import datetime
import json
import uuid

import jwt
from django.conf import settings
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import User
from .permissions import ROLE_PERMISSIONS
from .serializers import serialize_user


def error_response(status: int, code: str, message: str, details=None):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": details or {}, "request_id": str(uuid.uuid4())}},
        status=status,
    )


def token_for(user: User) -> str:
    now = datetime.datetime.now(datetime.timezone.utc)
    return jwt.encode(
        {"sub": str(user.pk), "iat": now, "exp": now + datetime.timedelta(hours=8)},
        settings.SECRET_KEY,
        algorithm="HS256",
    )


def user_from_request(request):
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        payload = jwt.decode(header[7:], settings.SECRET_KEY, algorithms=["HS256"])
        user = User.objects.get(pk=payload["sub"], status=User.STATUS_ACTIVE)
    except (jwt.PyJWTError, User.DoesNotExist, KeyError, ValueError):
        return None
    request.auth_user = user
    return user


@csrf_exempt
def login(request):
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return error_response(400, "invalid_json", "请求体不是有效 JSON")
    user = authenticate(request, username=body.get("email", ""), password=body.get("password", ""))
    if not user or user.status != User.STATUS_ACTIVE:
        return error_response(401, "invalid_credentials", "邮箱或密码错误")
    return JsonResponse({"data": {"access_token": token_for(user), "token_type": "Bearer", "expires_in": 28800, "user": serialize_user(user)}, "meta": {}})


def me(request):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    return JsonResponse({"data": serialize_user(user), "meta": {}})


def permissions(request):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    return JsonResponse({"data": {"role": user.role, "permissions": sorted(ROLE_PERMISSIONS.get(user.role, set()))}, "meta": {}})


def logout(request):
    if not user_from_request(request):
        return error_response(401, "unauthorized", "请先登录")
    return JsonResponse({}, status=204)
