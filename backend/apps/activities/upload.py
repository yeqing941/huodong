from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.views import error_response, user_from_request

from .models import Activity, ActivityScreenshot
from .views import activity_payload

MAX_IMAGE_SIZE = 10 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _can_edit(user, activity):
    return user and (user.role == "admin" or (user.role == "operator" and activity.created_by_id == user.pk))


@csrf_exempt
def activity_screenshots(request, activity_id):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    activity = get_object_or_404(Activity, pk=activity_id)
    if not _can_edit(user, activity):
        return error_response(403, "forbidden", "无权编辑此活动")
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    image = request.FILES.get("image")
    if not image:
        return error_response(400, "invalid_upload", "必须上传图片")
    if image.content_type not in ALLOWED_IMAGE_TYPES or image.size > MAX_IMAGE_SIZE:
        return error_response(400, "invalid_upload", "图片类型或大小无效")
    try:
        screenshot = ActivityScreenshot.objects.create(
            activity=activity,
            image=image,
            caption=request.POST.get("caption", ""),
            sort_order=int(request.POST.get("sort_order", 0)),
        )
    except (ValueError, ValidationError):
        return error_response(400, "invalid_upload", "截图字段无效")
    return JsonResponse({
        "data": {
            "id": str(screenshot.pk),
            "url": screenshot.image.url,
            "caption": screenshot.caption,
            "sort_order": screenshot.sort_order,
        },
        "meta": {},
    }, status=201)
