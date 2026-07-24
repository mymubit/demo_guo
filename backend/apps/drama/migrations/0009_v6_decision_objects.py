from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("drama", "0008_v6_runtime_hard_cut")]
    operations = [
        migrations.CreateModel(name="StudioDecision", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
            ("title", models.CharField(max_length=240)), ("kind", models.CharField(default="quality", max_length=64)),
            ("status", models.CharField(choices=[("open", "Open"), ("accepted", "Accepted"), ("dismissed", "Dismissed")], default="open", max_length=16)),
            ("severity", models.CharField(default="medium", max_length=16)), ("context", models.JSONField(default=dict)),
            ("created_by", models.CharField(default="system", max_length=128)), ("decided_by", models.CharField(blank=True, default="", max_length=128)),
            ("decided_at", models.DateTimeField(blank=True, null=True)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="studio_decisions", to="drama.dramaproject")),
        ]),
        migrations.CreateModel(name="StudioChangeSet", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("operation_id", models.CharField(max_length=128)), ("base_revision", models.PositiveIntegerField(default=0)),
            ("status", models.CharField(choices=[("candidate", "Candidate"), ("approved", "Approved"), ("committed", "Committed"), ("rejected", "Rejected")], default="candidate", max_length=16)), ("summary", models.CharField(blank=True, default="", max_length=500)), ("patch", models.JSONField(default=dict)), ("impact", models.JSONField(default=dict)), ("created_by", models.CharField(default="system", max_length=128)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="studio_changesets", to="drama.dramaproject")),
        ]),
        migrations.CreateModel(name="StudioEvidenceLink", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("run_id", models.UUIDField(blank=True, null=True)), ("call_id", models.UUIDField(blank=True, null=True)), ("artifact_key", models.CharField(blank=True, default="", max_length=128)), ("label", models.CharField(blank=True, default="", max_length=240)), ("created_at", models.DateTimeField(auto_now_add=True)),
            ("changeset", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="drama.studiochangeset")), ("decision", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="evidence", to="drama.studiodecision")), ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="studio_evidence", to="drama.dramaproject")),
        ]),
        migrations.CreateModel(name="StudioExperiment", fields=[
            ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)), ("name", models.CharField(max_length=240)), ("hypothesis", models.TextField(blank=True, default="")), ("baseline", models.JSONField(default=dict)), ("candidate", models.JSONField(default=dict)), ("metrics", models.JSONField(default=dict)), ("status", models.CharField(choices=[("draft", "Draft"), ("running", "Running"), ("ready", "Ready"), ("published", "Published")], default="draft", max_length=16)), ("created_by", models.CharField(default="system", max_length=128)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
        ]),
    ]
