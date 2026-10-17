from .models import AuditLog


def record_audit(actor, action, object_type, object_id="", success=True, before_data=None, after_data=None, note=""):
    return AuditLog.objects.create(
        actor=actor,
        action=action,
        object_type=object_type,
        object_id=str(object_id or ""),
        success=success,
        before_data=before_data or {},
        after_data=after_data or {},
        note=note,
    )
