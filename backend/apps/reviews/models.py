from django.db import models

from apps.activities.models import Activity, Tag
from apps.accounts.models import User


class ReviewRecord(models.Model):
    STATUS_PENDING_TAGGING = "pending_tagging"
    STATUS_PENDING_OPERATOR_REVIEW = "pending_operator_review"
    STATUS_PENDING_ADMIN_REVIEW = "pending_admin_review"
    STATUS_APPROVED = "approved"
    STATUS_RETURNED = "returned"
    STATUS_CHOICES = [(value, value) for value in (STATUS_PENDING_TAGGING, STATUS_PENDING_OPERATOR_REVIEW, STATUS_PENDING_ADMIN_REVIEW, STATUS_APPROVED, STATUS_RETURNED)]

    activity = models.ForeignKey(Activity, on_delete=models.PROTECT, related_name="review_records")
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="review_records_created")
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=STATUS_PENDING_TAGGING)
    original_data = models.JSONField(default=dict)
    candidate_tags = models.ManyToManyField(Tag, related_name="review_candidates", blank=True)
    candidate_confidences = models.JSONField(default=dict)
    candidate_reasons = models.JSONField(default=dict)
    ai_error = models.TextField(blank=True)
    operator_note = models.TextField(blank=True)
    admin_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
