import json

from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from apps.accounts.views import error_response, user_from_request
from apps.activities.models import GameType, Tag


def _admin(request):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if user.role != "admin":
        return user, error_response(403, "forbidden", "仅管理员可管理分类")
    return user, None


def _tag_data(tag):
    return {"id": str(tag.pk), "name": tag.name, "parent_id": str(tag.parent_id) if tag.parent_id else None, "level": tag.level, "description": tag.description, "ai_hints": tag.ai_hints, "is_active": tag.is_active, "sort_order": tag.sort_order}


def _game_type_data(item):
    return {"id": str(item.pk), "name": item.name, "is_active": item.is_active, "sort_order": item.sort_order}


def _json(request):
    try:
        return json.loads(request.body or "{}")
    except json.JSONDecodeError:
        raise ValueError("invalid_json")


def tags(request):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    if request.method == "GET":
        queryset = Tag.objects.all() if user.role == "admin" and request.GET.get("include_inactive") == "true" else Tag.objects.filter(is_active=True)
        return JsonResponse({"data": [_tag_data(tag) for tag in queryset], "meta": {}})
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = _json(request)
        level = int(body.get("level", 1))
        parent = Tag.objects.get(pk=body["parent_id"]) if body.get("parent_id") else None
        if level not in (1, 2, 3) or (level == 1 and parent) or (level > 1 and (not parent or parent.level != level - 1)):
            return error_response(400, "invalid_parent", "标签层级或父级无效")
        tag = Tag(name=str(body["name"]).strip(), parent=parent, level=level, description=body.get("description", ""), ai_hints=body.get("ai_hints", ""), sort_order=int(body.get("sort_order", 0)))
        tag.full_clean()
        tag.save()
    except (KeyError, Tag.DoesNotExist, ValueError):
        return error_response(400, "invalid_tag", "标签字段无效")
    return JsonResponse({"data": _tag_data(tag), "meta": {}}, status=201)


def tag_detail(request, tag_id):
    _, failure = _admin(request)
    if failure:
        return failure
    tag = get_object_or_404(Tag, pk=tag_id)
    if request.method != "PATCH":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = _json(request)
        parent = Tag.objects.get(pk=body["parent_id"]) if "parent_id" in body and body["parent_id"] else tag.parent
        level = int(body.get("level", tag.level))
        if level not in (1, 2, 3) or (level == 1 and parent) or (level > 1 and (not parent or parent.level != level - 1)):
            return error_response(400, "invalid_parent", "标签层级或父级无效")
        for field in ("name", "description", "ai_hints", "sort_order", "is_active"):
            if field in body:
                setattr(tag, field, body[field])
        tag.level, tag.parent = level, parent
        tag.full_clean()
        tag.save()
    except (Tag.DoesNotExist, ValueError):
        return error_response(400, "invalid_tag", "标签字段无效")
    return JsonResponse({"data": _tag_data(tag), "meta": {}})


def tag_disable(request, tag_id):
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    tag = get_object_or_404(Tag, pk=tag_id)
    if tag.level == 1 and tag.children.filter(is_active=True).exists():
        return error_response(409, "state_conflict", "仍有启用子标签，不能停用")
    tag.is_active = False
    tag.save(update_fields=["is_active"])
    return JsonResponse({"data": _tag_data(tag), "meta": {}})


def _move_tag(request, tag_id, merge=False):
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    source = get_object_or_404(Tag, pk=tag_id)
    try:
        target = Tag.objects.get(pk=_json(request)["target_id"])
        if source.pk == target.pk or source.level != target.level:
            return error_response(409, "state_conflict", "标签迁移目标状态冲突")
        with transaction.atomic():
            for activity in source.activities.all():
                activity.tags.add(target)
                activity.tags.remove(source)
            if merge:
                if source.children.exists() and target.children.filter(name__in=source.children.values_list("name", flat=True)).exists():
                    return error_response(409, "state_conflict", "合并后子标签名称冲突")
                source.children.update(parent=target)
                source.is_active = False
                source.save(update_fields=["is_active"])
            else:
                source.children.update(parent=target)
                source.is_active = False
                source.save(update_fields=["is_active"])
    except (KeyError, Tag.DoesNotExist, ValueError):
        return error_response(400, "invalid_tag", "迁移目标无效")
    return JsonResponse({"data": _tag_data(source), "meta": {}})


def tag_migrate(request, tag_id):
    return _move_tag(request, tag_id)


def tag_merge(request, tag_id):
    return _move_tag(request, tag_id, merge=True)


def game_types(request):
    user = user_from_request(request)
    if not user:
        return error_response(401, "unauthorized", "请先登录")
    if request.method == "GET":
        queryset = GameType.objects.all() if user.role == "admin" and request.GET.get("include_inactive") == "true" else GameType.objects.filter(is_active=True)
        return JsonResponse({"data": [_game_type_data(item) for item in queryset], "meta": {}})
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = _json(request)
        item = GameType.objects.create(name=str(body["name"]).strip(), sort_order=int(body.get("sort_order", 0)))
    except (KeyError, ValueError):
        return error_response(400, "invalid_game_type", "游戏类型字段无效")
    return JsonResponse({"data": _game_type_data(item), "meta": {}}, status=201)


def game_type_detail(request, game_type_id):
    _, failure = _admin(request)
    if failure:
        return failure
    item = get_object_or_404(GameType, pk=game_type_id)
    if request.method != "PATCH":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    try:
        body = _json(request)
        for field in ("name", "sort_order", "is_active"):
            if field in body:
                setattr(item, field, body[field])
        item.save()
    except ValueError:
        return error_response(400, "invalid_game_type", "游戏类型字段无效")
    return JsonResponse({"data": _game_type_data(item), "meta": {}})


def game_type_disable(request, game_type_id):
    _, failure = _admin(request)
    if failure:
        return failure
    if request.method != "POST":
        return error_response(405, "method_not_allowed", "请求方法不支持")
    item = get_object_or_404(GameType, pk=game_type_id)
    item.is_active = False
    item.save(update_fields=["is_active"])
    return JsonResponse({"data": _game_type_data(item), "meta": {}})
