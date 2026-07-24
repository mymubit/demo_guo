# Review package Task 1
Base: bf922f64abad28777f6e39a9827618c6e56822e2 (pre-task HEAD; commits skipped — working tree diff)
Head: working tree

## Changed files (stat)
 backend/apps/drama/models.py | 414 ++++++++++++++++++++++++++++++++++++++++++-
 1 file changed, 407 insertions(+), 7 deletions(-)

## Untracked / new

 M backend/apps/drama/models.py
?? backend/apps/drama/migrations/0020_v3_failover_attempt_and_backup_ids.py
?? backend/apps/drama/tests/test_v3_failover_models.py

## Full diff
```diff

diff --git a/backend/apps/drama/models.py b/backend/apps/drama/models.py
index c203a57..755224f 100644
--- a/backend/apps/drama/models.py
+++ b/backend/apps/drama/models.py
@@ -35,21 +35,21 @@ class DramaProject(models.Model):
         return self.title
 
 
-class DramaWorkflowState(models.Model):
-    """娴佺▼鐘舵€佹寔涔呭寲锛寁ersion 鐢ㄤ簬涔愯閿併€?""
+class DramaProjectRuntime(models.Model):
+    """V6 椤圭洰杩愯鏃讹紝浠呬繚瀛樺苟鍙?revision 涓庢渶杩戞彁浜ゅ厓鏁版嵁銆?""
 
     project = models.OneToOneField(
         DramaProject,
         on_delete=models.CASCADE,
-        related_name="workflow_state",
+        related_name="runtime",
         primary_key=True,
     )
-    state = models.JSONField("鐘舵€佸揩鐓?, default=dict)
-    version = models.PositiveIntegerField("鐘舵€佺増鏈?, default=0)
+    metadata = models.JSONField("杩愯鍏冩暟鎹?, default=dict)
+    revision = models.PositiveIntegerField("宸ヤ綔鍙扮増鏈?, default=0)
     updated_at = models.DateTimeField(auto_now=True)
 
     class Meta:
-        db_table = "drama_workflow_state"
+        db_table = "drama_project_runtime"
 
 
 class DramaArtifactVersion(models.Model):
@@ -84,6 +84,22 @@ class DramaArtifactVersion(models.Model):
         return f"{self.project_id}:{self.artifact_key}@v{self.version}"
 
 
+class DramaScriptDraft(models.Model):
+    """User-authored episode text, kept separate from immutable AI artifacts."""
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="script_drafts")
+    episode_number = models.PositiveIntegerField()
+    content = models.TextField(default="")
+    updated_by = models.CharField(max_length=128, default="")
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_script_draft"
+        constraints = [models.UniqueConstraint(fields=["project", "episode_number"], name="uniq_project_episode_draft")]
+        indexes = [models.Index(fields=["project", "episode_number"])]
+
+
 class DramaCommand(models.Model):
     """宸ヤ綔娴佸懡浠ゅ箓绛夎褰曘€?""
 
@@ -171,7 +187,7 @@ class DramaGenerationJob(models.Model):
     command_id = models.CharField("鍛戒护 ID", max_length=128, blank=True, default="")
     role = models.CharField("瑙掕壊", max_length=64, blank=True, default="")
     artifact_key = models.CharField("浜х墿閿?, max_length=64, blank=True, default="")
-    workflow_version = models.PositiveIntegerField("宸ヤ綔娴佺増鏈?, null=True, blank=True)
+    base_revision = models.PositiveIntegerField("鎵ц鍩虹嚎鐗堟湰", null=True, blank=True)
     created_at = models.DateTimeField(auto_now_add=True)
     updated_at = models.DateTimeField(auto_now=True)
 
@@ -291,6 +307,20 @@ class DramaLlmCallLog(models.Model):
         null=True,
         blank=True,
     )
+    v3_command_run = models.ForeignKey(
+        "V3CommandRun",
+        on_delete=models.SET_NULL,
+        related_name="llm_call_logs",
+        null=True,
+        blank=True,
+    )
+    v3_project = models.ForeignKey(
+        "V3Project",
+        on_delete=models.SET_NULL,
+        related_name="llm_call_logs",
+        null=True,
+        blank=True,
+    )
     actor = models.CharField("鎿嶄綔浜?, max_length=128, default="system")
     role = models.CharField("鎶€鑳借鑹?, max_length=64, blank=True, default="")
     purpose = models.CharField(
@@ -328,6 +358,8 @@ class DramaLlmCallLog(models.Model):
         indexes = [
             models.Index(fields=["project", "-created_at"]),
             models.Index(fields=["generation_job", "seq_in_job"]),
+            models.Index(fields=["v3_command_run", "-created_at"]),
+            models.Index(fields=["v3_project", "-created_at"]),
             models.Index(fields=["role", "-created_at"]),
             models.Index(fields=["status", "-created_at"]),
         ]
@@ -336,3 +368,371 @@ class DramaLlmCallLog(models.Model):
 
     def __str__(self) -> str:
         return f"{self.role or self.purpose} @ {self.created_at:%Y-%m-%d %H:%M:%S}"
+
+
+class StudioDecision(models.Model):
+    """Human decisions are first-class V6 work items."""
+    class Status(models.TextChoices):
+        OPEN = "open", "Open"
+        ACCEPTED = "accepted", "Accepted"
+        DISMISSED = "dismissed", "Dismissed"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_decisions")
+    title = models.CharField(max_length=240)
+    kind = models.CharField(max_length=64, default="quality")
+    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
+    severity = models.CharField(max_length=16, default="medium")
+    context = models.JSONField(default=dict)
+    created_by = models.CharField(max_length=128, default="system")
+    decided_by = models.CharField(max_length=128, blank=True, default="")
+    decided_at = models.DateTimeField(null=True, blank=True)
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        ordering = ["status", "-created_at"]
+
+
+class StudioChangeSet(models.Model):
+    """Candidate edits remain separate from committed artifact versions."""
+    class Status(models.TextChoices):
+        CANDIDATE = "candidate", "Candidate"
+        APPROVED = "approved", "Approved"
+        COMMITTED = "committed", "Committed"
+        REJECTED = "rejected", "Rejected"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_changesets")
+    operation_id = models.CharField(max_length=128)
+    base_revision = models.PositiveIntegerField(default=0)
+    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CANDIDATE)
+    summary = models.CharField(max_length=500, blank=True, default="")
+    patch = models.JSONField(default=dict)
+    impact = models.JSONField(default=dict)
+    created_by = models.CharField(max_length=128, default="system")
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+
+class StudioEvidenceLink(models.Model):
+    """Links every UI decision to an auditable run, call, or artifact."""
+    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_evidence")
+    decision = models.ForeignKey(StudioDecision, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
+    changeset = models.ForeignKey(StudioChangeSet, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
+    run_id = models.UUIDField(null=True, blank=True)
+    call_id = models.UUIDField(null=True, blank=True)
+    artifact_key = models.CharField(max_length=128, blank=True, default="")
+    label = models.CharField(max_length=240, blank=True, default="")
+    created_at = models.DateTimeField(auto_now_add=True)
+
+
+class StudioExperiment(models.Model):
+    """Governance changes are tested against evidence before publication."""
+    class Status(models.TextChoices):
+        DRAFT = "draft", "Draft"
+        RUNNING = "running", "Running"
+        READY = "ready", "Ready"
+        PUBLISHED = "published", "Published"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    name = models.CharField(max_length=240)
+    hypothesis = models.TextField(blank=True, default="")
+    baseline = models.JSONField(default=dict)
+    candidate = models.JSONField(default=dict)
+    metrics = models.JSONField(default=dict)
+    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
+    created_by = models.CharField(max_length=128, default="system")
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+
+class V3Project(models.Model):
+    """V3 浜у搧闈㈤」鐩紙涓?V6 DramaProject 瑙ｈ€︾殑鏈€灏忛鍩熻〃锛夈€?""
+
+    class EntryType(models.TextChoices):
+        ORIGINAL = "original", "鍘熷垱"
+        ADAPT = "adapt", "鏀圭紪"
+
+    class Stage(models.TextChoices):
+        TOPIC = "topic", "閫夐"
+        BLUEPRINT = "blueprint", "钃濆浘"
+        EPISODES = "episodes", "鍒嗛泦"
+        WRITING = "writing", "姝ｆ枃"
+        QUALITY = "quality", "璐ㄦ"
+        DELIVERY = "delivery", "浜や粯"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    owner = models.ForeignKey(
+        settings.AUTH_USER_MODEL,
+        on_delete=models.CASCADE,
+        related_name="v3_projects",
+    )
+    title = models.CharField(max_length=200)
+    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
+    stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.TOPIC)
+    progress_percent = models.PositiveSmallIntegerField(default=0)
+    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_v3_project"
+        ordering = ["-updated_at"]
+
+    def __str__(self) -> str:
+        return self.title
+
+
+class V3CommandRun(models.Model):
+    """V3 鍛戒护鎵ц璁板綍锛堝紓姝?骞傜瓑杩借釜锛夈€?""
+
+    class Status(models.TextChoices):
+        QUEUED = "queued", "鎺掗槦"
+        RUNNING = "running", "鎵ц涓?
+        SUCCEEDED = "succeeded", "鎴愬姛"
+        FAILED = "failed", "澶辫触"
+        UNSUPPORTED = "unsupported", "鏈樁娈垫湭瀹炵幇"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    owner = models.ForeignKey(
+        settings.AUTH_USER_MODEL,
+        on_delete=models.CASCADE,
+        related_name="v3_command_runs",
+    )
+    project = models.ForeignKey(
+        V3Project,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+        related_name="command_runs",
+    )
+    command_type = models.CharField(max_length=64)
+    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
+    idempotency_key = models.CharField(max_length=64, blank=True, default="")
+    request_payload = models.JSONField(default=dict)
+    result_payload = models.JSONField(default=dict)
+    error_message = models.TextField(blank=True, default="")
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_v3_command_run"
+        ordering = ["-created_at"]
+        indexes = [
+            models.Index(fields=["owner", "-created_at"]),
+            models.Index(fields=["command_type", "status"]),
+        ]
+
+    def __str__(self) -> str:
+        return f"{self.command_type} ({self.status})"
+
+
+class V3ArtifactVersion(models.Model):
+    """V3 浜х墿鐗堟湰锛坉raft / candidate / committed / superseded锛夈€?""
+
+    class Status(models.TextChoices):
+        DRAFT = "draft", "鑽夌"
+        CANDIDATE = "candidate", "鍊欓€?
+        COMMITTED = "committed", "宸茬‘璁?
+        SUPERSEDED = "superseded", "宸叉浛浠?
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(
+        V3Project,
+        on_delete=models.CASCADE,
+        related_name="artifacts",
+    )
+    artifact_key = models.CharField(max_length=64)
+    version = models.PositiveIntegerField()
+    schema_version = models.PositiveIntegerField(default=1)
+    status = models.CharField(max_length=16, choices=Status.choices)
+    payload = models.JSONField(default=dict)
+    command_run = models.ForeignKey(
+        V3CommandRun,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+        related_name="artifacts",
+    )
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        db_table = "drama_v3_artifact_version"
+        constraints = [
+            models.UniqueConstraint(
+                fields=["project", "artifact_key", "version"],
+                name="uniq_v3_artifact_version",
+            ),
+        ]
+
+    def __str__(self) -> str:
+        return f"{self.artifact_key} v{self.version} ({self.status})"
+
+
+class V3ScriptDraft(models.Model):
+    """V3 姝ｆ枃浜哄伐鑽夌锛堟寜闆嗗彿锛屼笌 AI episode_scripts 鍊欓€夊垎绂伙級銆?""
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(
+        V3Project,
+        on_delete=models.CASCADE,
+        related_name="script_drafts",
+    )
+    episode_number = models.PositiveIntegerField()
+    payload = models.JSONField(default=dict)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_v3_script_draft"
+        constraints = [
+            models.UniqueConstraint(
+                fields=["project", "episode_number"],
+                name="uniq_v3_project_episode_script_draft",
+            ),
+        ]
+
+    def __str__(self) -> str:
+        return f"ep{self.episode_number} draft ({self.project_id})"
+
+
+class V3QualityFinding(models.Model):
+    """V3 璐ㄦ/鍚堣闂锛堝彲鎺ュ彈銆佸彲杩借釜澶勭悊鐘舵€侊級銆?""
+
+    class Source(models.TextChoices):
+        QUALITY = "quality", "璐ㄩ噺"
+        COMPLIANCE = "compliance", "鍚堣"
+
+    class Status(models.TextChoices):
+        OPEN = "open", "寰呭鐞?
+        ACCEPTED = "accepted", "宸叉帴鍙?
+        RESOLVED = "resolved", "宸茶В鍐?
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    project = models.ForeignKey(
+        V3Project,
+        on_delete=models.CASCADE,
+        related_name="quality_findings",
+    )
+    source = models.CharField(max_length=16, choices=Source.choices)
+    finding_key = models.CharField(max_length=128)  # 绋冲畾閿細濡?defect index 鎴?hash
+    title = models.CharField(max_length=256)
+    severity = models.CharField(max_length=32, blank=True, default="")
+    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
+    report_artifact = models.ForeignKey(
+        V3ArtifactVersion,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+    )
+    created_at = models.DateTimeField(auto_now_add=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_v3_quality_finding"
+        constraints = [
+            models.UniqueConstraint(
+                fields=["project", "source", "finding_key"],
+                name="uniq_v3_finding_project_source_key",
+            )
+        ]
+
+    def __str__(self) -> str:
+        return f"{self.source}:{self.finding_key} ({self.status})"
+
+
+class V3SystemConfigRevision(models.Model):
+    """V3 鍏ㄥ眬绯荤粺閰嶇疆涓嶅彲鍙樹慨璁紙overlay 鍙?foundation presets锛夈€?""
+
+    revision = models.PositiveIntegerField(unique=True)
+    overlay = models.JSONField(default=dict)
+    updated_by = models.CharField(max_length=128)
+    change_reason = models.CharField(max_length=500, blank=True, default="")
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        db_table = "drama_v3_system_config_revision"
+        ordering = ["-revision"]
+
+    def __str__(self) -> str:
+        return f"system_config r{self.revision}"
+
+
+class V3RoleModelMapping(models.Model):
+    """V3 鎶€鑳借鑹?鈫?LLM Provider 鏄犲皠锛堟棤鏄犲皠鏃惰繍琛屾椂鐢?active provider锛夈€?""
+
+    role_key = models.CharField(max_length=64, unique=True)
+    provider = models.ForeignKey(
+        DramaLlmProvider,
+        on_delete=models.CASCADE,
+        related_name="role_mappings",
+    )
+    temperature = models.FloatField(null=True, blank=True)
+    max_tokens = models.PositiveIntegerField(null=True, blank=True)
+    backup_provider_ids = models.JSONField(default=list, blank=True)
+    updated_at = models.DateTimeField(auto_now=True)
+
+    class Meta:
+        db_table = "drama_v3_role_model_mapping"
+
+    def __str__(self) -> str:
+        return self.role_key
+
+
+class V3FailoverAttempt(models.Model):
+    """V3 LLM 涓诲閾惧崟娆″垏鎹㈠皾璇曞璁°€?""
+
+    class Status(models.TextChoices):
+        SUCCEEDED = "succeeded", "鎴愬姛"
+        FAILED_SWITCHABLE = "failed_switchable", "鍙垏鎹㈠け璐?
+        FAILED_TERMINAL = "failed_terminal", "缁堟€佸け璐?
+        SKIPPED = "skipped", "璺宠繃"
+
+    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
+    v3_command_run = models.ForeignKey(
+        V3CommandRun,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+        related_name="failover_attempts",
+    )
+    v3_project = models.ForeignKey(
+        V3Project,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+        related_name="failover_attempts",
+    )
+    owner = models.ForeignKey(
+        settings.AUTH_USER_MODEL,
+        on_delete=models.CASCADE,
+        related_name="v3_failover_attempts",
+    )
+    role_key = models.CharField(max_length=64)
+    provider = models.ForeignKey(
+        DramaLlmProvider,
+        on_delete=models.CASCADE,
+        related_name="failover_attempts",
+    )
+    attempt_index = models.PositiveIntegerField()
+    status = models.CharField(max_length=32, choices=Status.choices)
+    error_code = models.CharField(max_length=64, blank=True, default="")
+    error_message = models.TextField(blank=True, default="")
+    llm_call_log = models.ForeignKey(
+        DramaLlmCallLog,
+        null=True,
+        blank=True,
+        on_delete=models.SET_NULL,
+        related_name="failover_attempts",
+    )
+    created_at = models.DateTimeField(auto_now_add=True)
+
+    class Meta:
+        db_table = "drama_v3_failover_attempt"
+        ordering = ["-created_at"]
+        indexes = [
+            models.Index(fields=["v3_command_run", "-created_at"]),
+        ]
+
+    def __str__(self) -> str:
+        return f"{self.role_key}#{self.attempt_index} ({self.status})"

### NEW FILE migration

# Generated by Django 6.0.5 on 2026-07-23 07:32

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('drama', '0019_dramallmcalllog_v3_fks'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='v3rolemodelmapping',
            name='backup_provider_ids',
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name='V3FailoverAttempt',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('role_key', models.CharField(max_length=64)),
                ('attempt_index', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('succeeded', '鎴愬姛'), ('failed_switchable', '鍙垏鎹㈠け璐?), ('failed_terminal', '缁堟€佸け璐?), ('skipped', '璺宠繃')], max_length=32)),
                ('error_code', models.CharField(blank=True, default='', max_length=64)),
                ('error_message', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('llm_call_log', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='failover_attempts', to='drama.dramallmcalllog')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='v3_failover_attempts', to=settings.AUTH_USER_MODEL)),
                ('provider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='failover_attempts', to='drama.dramallmprovider')),
                ('v3_command_run', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='failover_attempts', to='drama.v3commandrun')),
                ('v3_project', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='failover_attempts', to='drama.v3project')),
            ],
            options={
                'db_table': 'drama_v3_failover_attempt',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['v3_command_run', '-created_at'], name='drama_v3_fa_v3_comm_86eb6c_idx')],
            },
        ),
    ]


### NEW FILE test

# -*- coding: utf-8 -*-
"""P2-W1 Task 1锛歜ackup_provider_ids + V3FailoverAttempt 妯″瀷銆?""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.drama.models import (
    DramaLlmProvider,
    V3FailoverAttempt,
    V3Project,
    V3RoleModelMapping,
)


class FailoverModelTests(TestCase):
    def test_mapping_backup_ids_default_empty_and_attempt_create(self) -> None:
        user = get_user_model().objects.create_user("m1", password="x")
        p1 = DramaLlmProvider.objects.create(
            name="A",
            base_url="https://a.example",
            model_name="m",
            api_key_encrypted="x",
            is_enabled=True,
        )
        mapping = V3RoleModelMapping.objects.create(
            role_key="drama-script-writer",
            provider=p1,
        )
        self.assertEqual(mapping.backup_provider_ids, [])
        project = V3Project.objects.create(
            owner=user,
            title="t",
            entry_type="original",
            stage="topic",
        )
        attempt = V3FailoverAttempt.objects.create(
            owner=user,
            v3_project=project,
            role_key="drama-script-writer",
            provider=p1,
            attempt_index=0,
            status=V3FailoverAttempt.Status.SUCCEEDED,
        )
        self.assertEqual(attempt.status, "succeeded")

```

