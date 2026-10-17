from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [("activities", "0002_activityimport"), ("accounts", "0001_initial")]
    operations = [migrations.CreateModel(name="ReviewRecord", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("status", models.CharField(choices=[(x, x) for x in ("pending_tagging", "pending_operator_review", "pending_admin_review", "approved", "returned")], default="pending_tagging", max_length=40)),
        ("original_data", models.JSONField(default=dict)), ("candidate_confidences", models.JSONField(default=dict)), ("candidate_reasons", models.JSONField(default=dict)), ("ai_error", models.TextField(blank=True)), ("operator_note", models.TextField(blank=True)), ("admin_note", models.TextField(blank=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ("activity", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_records", to="activities.activity")),
        ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="review_records_created", to="accounts.user")),
    ], options={"ordering": ["-created_at"]}), migrations.AddField(model_name="reviewrecord", name="candidate_tags", field=models.ManyToManyField(blank=True, related_name="review_candidates", to="activities.tag"))]
