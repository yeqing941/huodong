import hashlib
import time
import uuid

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.http.response import Http404


RATE_LIMIT_PATHS = {
    "/api/v1/activities",
    "/api/v1/favorites",
    "/api/v1/reviews",
    "/api/v1/crawler/tasks",
}


def _error(status, code, message):
    return JsonResponse(
        {"error": {"code": code, "message": message, "details": {}, "request_id": str(uuid.uuid4())}},
        status=status,
    )


class CoreRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._is_rate_limited_path(request.path):
            limit = max(int(getattr(settings, "CORE_RATE_LIMIT", 60)), 1)
            window = max(int(getattr(settings, "CORE_RATE_LIMIT_WINDOW", 60)), 1)
            identity = request.headers.get("Authorization", "") or self._client_ip(request)
            digest = hashlib.sha256(identity.encode()).hexdigest()[:24]
            key = f"core-rate:{request.path}:{digest}"
            now = int(time.time())
            bucket = cache.get(key)
            if not bucket or bucket["expires"] <= now:
                bucket = {"count": 0, "expires": now + window}
            if bucket["count"] >= limit:
                response = _error(429, "rate_limited", "请求过于频繁，请稍后再试")
                response["Retry-After"] = str(max(bucket["expires"] - now, 1))
                return response
            bucket["count"] += 1
            cache.set(key, bucket, max(bucket["expires"] - now, 1))
        try:
            return self.get_response(request)
        except Http404:
            return _error(404, "not_found", "资源不存在")
        except (ValueError, TypeError):
            return _error(400, "invalid_parameter", "请求参数无效")

    @staticmethod
    def _client_ip(request):
        return request.META.get("REMOTE_ADDR", "unknown")

    @staticmethod
    def _is_rate_limited_path(path):
        return path in RATE_LIMIT_PATHS or path.startswith("/api/v1/activities/") or path.startswith("/api/v1/reviews/") or path.startswith("/api/v1/crawler/tasks/")

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return _error(404, "not_found", "资源不存在")
        if isinstance(exception, (ValueError, TypeError)):
            return _error(400, "invalid_parameter", "请求参数无效")
        return None
