import csv
import io

from django.db import transaction

from .models import Activity, ActivityImport, GameType, Tag


def import_activity_csv(upload, user):
    decoded = upload.read().decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(decoded))
    issues = []
    valid_rows = []
    for row_number, row in enumerate(reader, start=2):
        activity_name = row.get("activity_name", "").strip()
        game_name = row.get("game_name", "").strip()
        tag_name = row.get("tag", "").strip()
        game_type_name = row.get("game_type", "").strip()
        source_url = row.get("source_url", "").strip()
        source_site = row.get("source_site", "manual").strip() or "manual"
        row_issues = []
        if not activity_name:
            row_issues.append("活动名称缺失")
        if not game_name:
            row_issues.append("游戏名称缺失")
        if not source_url:
            row_issues.append("来源 URL 缺失")
        if source_site not in dict(Activity.SOURCE_CHOICES):
            row_issues.append("来源站点无效")
        tag = Tag.objects.filter(name=tag_name, is_active=True).first() if tag_name else None
        if not tag:
            row_issues.append("标签不存在或已停用")
        game_type = GameType.objects.filter(name=game_type_name, is_active=True).first() if game_type_name else None
        if not game_type:
            row_issues.append("游戏类型不存在或已停用")
        if row_issues:
            issues.append({"row": row_number, "message": "；".join(row_issues)})
        else:
            valid_rows.append((row, game_type, tag))

    with transaction.atomic():
        for row, game_type, tag in valid_rows:
            activity = Activity.objects.create(
                source_url=row.get("source_url", "").strip(),
                source_site=row.get("source_site", "manual").strip() or "manual",
                game_name=row["game_name"].strip(),
                game_type=game_type,
                activity_name=row["activity_name"].strip(),
                description=row.get("description", "").strip(),
                created_by=user,
                status=Activity.STATUS_ACTIVE,
            )
            activity.tags.add(tag)
        status = ActivityImport.STATUS_COMPLETED if not issues else (ActivityImport.STATUS_PARTIAL if valid_rows else ActivityImport.STATUS_FAILED)
        result = ActivityImport.objects.create(
            created_by=user,
            filename=upload.name,
            status=status,
            valid_count=len(valid_rows),
            issue_count=len(issues),
            issues=issues,
        )
    return result
