import json

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from apps.accounts.permissions import has_permission
from apps.accounts.views import error_response, user_from_request
from apps.activities.models import Activity, Tag

from .models import ReviewRecord
from .services import run_ai_tagging


def _user(request, permission):
    user = user_from_request(request)
    if not user:
        return None, error_response(401, "unauthorized", "请先登录")
    if not has_permission(user, permission):
        return None, error_response(403, "forbidden", "无权执行此操作")
    return user, None


def _payload(review):
    return {
        "id": str(review.pk), "activity_id": str(review.activity_id), "status": review.status,
        "candidate_tags": [{"id": str(tag.pk), "name": tag.name, "confidence": review.candidate_confidences.get(str(tag.pk)), "reason": review.candidate_reasons.get(str(tag.pk), "")} for tag in review.candidate_tags.all()],
        "ai_error": review.ai_error, "operator_note": review.operator_note, "admin_note": review.admin_note,
        "original_data": review.original_data,
    }


@csrf_exempt
def reviews(request, review_id=None):
    user, failure = _user(request, "review:operator")
    if failure:
        return failure
    if request.method == "POST" and review_id is None:
        try:
            body = json.loads(request.body or "{}")
            activity = Activity.objects.get(pk=body["activity_id"])
        except (KeyError, ValueError, Activity.DoesNotExist, json.JSONDecodeError):
            return error_response(400, "invalid_review", "活动无效")
        review = ReviewRecord.objects.create(
            activity=activity, created_by=user,
            original_data={"activity_name": activity.activity_name, "game_name": activity.game_name, "description": activity.description, "source_url": activity.source_url},
        )
        return JsonResponse({"data": _payload(review), "meta": {}}, status=201)
    if request.method == "GET" and review_id is None:
        return JsonResponse({"data": [_payload(item) for item in ReviewRecord.objects.prefetch_related("candidate_tags")], "meta": {}})
    if review_id is None:
        return error_response(405, "method_not_allowed", "请求方法不支持")
    review = get_object_or_404(ReviewRecord.objects.prefetch_related("candidate_tags"), pk=review_id)
    return JsonResponse({"data": _payload(review), "meta": {}})


@csrf_exempt
def ai_tag(request, review_id):
    user, failure = _user(request, "review:operator")
    if failure:
        return failure
    review = get_object_or_404(ReviewRecord, pk=review_id)
    if review.status not in {ReviewRecord.STATUS_PENDING_TAGGING, ReviewRecord.STATUS_RETURNED}:
        return error_response(409, "invalid_state", "当前状态不能执行 AI 打标")
    try:
        body = json.loads(request.body or "{}")
        suggestions = run_ai_tagging(review, force_failure=body.get("force_failure", False))
        review.candidate_tags.set([item["tag"] for item in suggestions])
        review.candidate_confidences = {str(item["tag"].pk): item["confidence"] for item in suggestions}
        review.candidate_reasons = {str(item["tag"].pk): item["reason"] for item in suggestions}
        review.ai_error = ""
        review.status = ReviewRecord.STATUS_PENDING_OPERATOR_REVIEW
    except Exception as exc:
        review.ai_error = str(exc)
    review.save(update_fields=["candidate_confidences", "candidate_reasons", "ai_error", "status", "updated_at"])
    return JsonResponse({"data": _payload(review), "meta": {}})


@csrf_exempt
def operator_review(request, review_id):
    user, failure = _user(request, "review:operator")
    if failure:
        return failure
    review = get_object_or_404(ReviewRecord, pk=review_id)
    if review.status != ReviewRecord.STATUS_PENDING_OPERATOR_REVIEW:
        return error_response(409, "invalid_state", "当前状态不能由运营处理")
    try:
        body = json.loads(request.body or "{}")
        action = body.get("action")
        if action == "cancel":
            review.status = ReviewRecord.STATUS_RETURNED
        elif action == "submit":
            tag_ids = body.get("tag_ids", [])
            tags = list(Tag.objects.filter(pk__in=tag_ids, is_active=True))
            if not tags or len(tags) != len(set(tag_ids)):
                return error_response(400, "invalid_tags", "只能选择启用标签")
            review.candidate_tags.set(tags)
            review.operator_note = body.get("note", "")
            review.status = ReviewRecord.STATUS_PENDING_ADMIN_REVIEW
        else:
            return error_response(400, "invalid_action", "运营操作无效")
    except json.JSONDecodeError:
        return error_response(400, "invalid_json", "请求体不是有效 JSON")
    review.save(update_fields=["operator_note", "status", "updated_at"])
    return JsonResponse({"data": _payload(review), "meta": {}})


@csrf_exempt
def admin_review(request, review_id):
    user, failure = _user(request, "*")
    if failure:
        return failure
    review = get_object_or_404(ReviewRecord, pk=review_id)
    if review.status != ReviewRecord.STATUS_PENDING_ADMIN_REVIEW:
        return error_response(409, "invalid_state", "当前状态不能由管理员处理")
    try:
        body = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return error_response(400, "invalid_json", "请求体不是有效 JSON")
    action = body.get("action")
    if action == "return":
        review.status = ReviewRecord.STATUS_RETURNED
        review.admin_note = body.get("reason", "")
    elif action == "approve":
        review.activity.tags.set(review.candidate_tags.all())
        review.activity.status = Activity.STATUS_ACTIVE
        review.activity.save(update_fields=["status", "updated_at"])
        review.status = ReviewRecord.STATUS_APPROVED
    elif action == "correct":
        tag_ids = body.get("tag_ids", [])
        tags = list(Tag.objects.filter(pk__in=tag_ids, is_active=True))
        if not tags:
            return error_response(400, "invalid_tags", "修正后至少需要一个启用标签")
        review.candidate_tags.set(tags)
        review.status = ReviewRecord.STATUS_APPROVED
        review.activity.tags.set(tags)
        review.activity.status = Activity.STATUS_ACTIVE
        review.activity.save(update_fields=["status", "updated_at"])
    else:
        return error_response(400, "invalid_action", "管理员操作无效")
    review.save(update_fields=["admin_note", "status", "updated_at"])
    return JsonResponse({"data": _payload(review), "meta": {}})
