import json
import uuid

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.accounts.permissions import has_permission
from apps.accounts.views import error_response, user_from_request

from .models import Activity, Favorite, GameType, Tag


def activity_payload(activity, request=None):
    screenshots = [
        {
            "id": str(item.pk),
            "url": item.image.url if hasattr(item.image, "url") else str(item.image),
            "caption": item.caption,
            "sort_order": item.sort_order,
        }
        for item in activity.screenshots.all()
    ]
    return {
        "id": str(activity.pk),
        "source_url": activity.source_url,
        "source_site": activity.source_site,
        "game_name": activity.game_name,
        "game_type": {"id": str(activity.game_type_id), "name": activity.game_type.name},
        "activity_name": activity.activity_name,
        "activity_start": activity.activity_start.isoformat() if activity.activity_start else None,
        "activity_end": activity.activity_end.isoformat() if activity.activity_end else None,
        "description": activity.description,
        "status": activity.status,
        "tags": [{"id": str(tag.pk), "name": tag.name, "level": tag.level} for tag in activity.tags.all()],
        "screenshots": screenshots,
        "is_favorite": bool(request and Favorite.objects.filter(user=request.auth_user, activity=activity).exists()),
        "created_at": activity.created_at.isoformat(),
    }


def list_payload(queryset, request, page, page_size):
    paginator = Paginator(queryset, page_size)
    current = paginator.get_page(page)
    return {
        "items": [activity_payload(item, request) for item in current.object_list],
        "page": current.number,
        "page_size": page_size,
        "total": paginator.count,
        "total_pages": paginator.num_pages,
    }


def require_user(request, permission=None):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if permission and not has_permission(user, permission):
        return None, error_response(403, "forbidden", "无权执行此操作")
    return user, None


def activities(request):
    user, failure = require_user(request, "activity:read")
    if failure:
        return failure
    if request.method == "POST":
        if not has_permission(user, "activity:write"):
            return error_response(403, "forbidden", "无权创建活动")
        try:
            body = json.loads(request.body or "{}")
            game_type = GameType.objects.get(pk=body["game_type_id"], is_active=True)
            tag_list = list(Tag.objects.filter(pk__in=body.get("tag_ids", []), is_active=True))
            if not body.get("screenshot") or not tag_list:
                return error_response(400, "invalid_activity", "活动至少需要一张截图和一个启用标签")
            activity = Activity.objects.create(
                source_url=body["source_url"],
                source_site=body.get("source_site", "manual"),
                game_name=body["game_name"],
                game_type=game_type,
                activity_name=body["activity_name"],
                description=body.get("description", ""),
                created_by=user,
                status=Activity.STATUS_ACTIVE,
            )
            activity.tags.set(tag_list)
            activity.screenshots.create(image=body["screenshot"], sort_order=1)
            return JsonResponse({"data": activity_payload(activity, request), "meta": {}}, status=201)
        except (KeyError, GameType.DoesNotExist, ValueError, json.JSONDecodeError):
            return error_response(400, "invalid_activity", "活动字段无效")
    if request.method != "GET":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    queryset = Activity.objects.select_related("game_type").prefetch_related("tags", "screenshots")
    if request.GET.get("status"):
        queryset = queryset.filter(status=request.GET["status"])
    elif request.GET.get("include_archived") != "true" or user.role != "admin":
        queryset = queryset.exclude(status=Activity.STATUS_ARCHIVED)
    if request.GET.get("game_type_id"):
        queryset = queryset.filter(game_type_id=request.GET["game_type_id"])
    if request.GET.get("game_name"):
        queryset = queryset.filter(game_name__icontains=request.GET["game_name"])
    if request.GET.get("activity_name"):
        queryset = queryset.filter(activity_name__icontains=request.GET["activity_name"])
    for tag_id in request.GET.getlist("tag_id"):
        queryset = queryset.filter(tags__id=tag_id)
    sort = request.GET.get("sort", "created_at")
    order = "-" if request.GET.get("order", "desc") == "desc" else ""
    if sort in {"created_at", "game_name", "activity_name"}:
        queryset = queryset.order_by(f"{order}{sort}")
    page = max(int(request.GET.get("page", 1)), 1)
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    return JsonResponse({"data": list_payload(queryset.distinct(), request, page, page_size), "meta": {}})


def activity_detail(request, activity_id):
    user, failure = require_user(request, "activity:read")
    if failure:
        return failure
    activity = get_object_or_404(Activity.objects.select_related("game_type").prefetch_related("tags", "screenshots"), pk=activity_id)
    return JsonResponse({"data": activity_payload(activity, request), "meta": {}})


def favorite(request, activity_id):
    user, failure = require_user(request, "favorite:write")
    if failure:
        return failure
    activity = get_object_or_404(Activity, pk=activity_id, status=Activity.STATUS_ACTIVE)
    if request.method == "POST":
        if Favorite.objects.filter(user=user, activity=activity).exists():
            return error_response(409, "already_favorited", "活动已收藏")
        Favorite.objects.create(user=user, activity=activity)
        return JsonResponse({}, status=204)
    if request.method == "DELETE":
        Favorite.objects.filter(user=user, activity=activity).delete()
        return JsonResponse({}, status=204)
    return error_response(405, "method_not_allowed", "请求方法不支持")


def favorites(request):
    user, failure = require_user(request, "favorite:write")
    if failure:
        return failure
    queryset = Activity.objects.filter(favorites__user=user).select_related("game_type").prefetch_related("tags", "screenshots")
    page = max(int(request.GET.get("page", 1)), 1)
    page_size = min(max(int(request.GET.get("page_size", 20)), 1), 100)
    return JsonResponse({"data": list_payload(queryset, request, page, page_size), "meta": {}})


def tags(request):
    user, failure = require_user(request, "activity:read")
    if failure:
        return failure
    data = [{"id": str(tag.pk), "name": tag.name, "parent_id": str(tag.parent_id) if tag.parent_id else None, "level": tag.level} for tag in Tag.objects.filter(is_active=True)]
    return JsonResponse({"data": data, "meta": {}})


def game_types(request):
    user, failure = require_user(request, "activity:read")
    if failure:
        return failure
    data = [{"id": str(item.pk), "name": item.name} for item in GameType.objects.filter(is_active=True)]
    return JsonResponse({"data": data, "meta": {}})
