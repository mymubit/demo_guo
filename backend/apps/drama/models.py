# -*- coding: utf-8 -*-
"""短剧领域模型。"""
from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models


class DramaProject(models.Model):
    """短剧项目主表。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="drama_projects",
    )
    title = models.CharField("标题", max_length=200)
    settings = models.JSONField("项目设置", default=dict)
    settings_revision = models.PositiveIntegerField("设置版本", default=1)
    skills_version = models.CharField("技能版本", max_length=32, default="5.0.0")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_project"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class DramaProjectRuntime(models.Model):
    """V6 项目运行时，仅保存并发 revision 与最近提交元数据。"""

    project = models.OneToOneField(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="runtime",
        primary_key=True,
    )
    metadata = models.JSONField("运行元数据", default=dict)
    revision = models.PositiveIntegerField("工作台版本", default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_project_runtime"


class DramaArtifactVersion(models.Model):
    """产物版本表。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="artifact_versions",
    )
    artifact_key = models.CharField("产物键", max_length=64, db_index=True)
    version = models.PositiveIntegerField("版本号", default=1)
    schema_version = models.PositiveIntegerField("Schema 版本")
    payload = models.JSONField("内容")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_artifact_version"
        ordering = ["artifact_key", "-version"]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "artifact_key", "version"],
                name="uniq_artifact_version",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "artifact_key", "-version"]),
        ]

    def __str__(self) -> str:
        return f"{self.project_id}:{self.artifact_key}@v{self.version}"


class DramaScriptDraft(models.Model):
    """User-authored episode text, kept separate from immutable AI artifacts."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="script_drafts")
    episode_number = models.PositiveIntegerField()
    content = models.TextField(default="")
    updated_by = models.CharField(max_length=128, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_script_draft"
        constraints = [models.UniqueConstraint(fields=["project", "episode_number"], name="uniq_project_episode_draft")]
        indexes = [models.Index(fields=["project", "episode_number"])]


class DramaCommand(models.Model):
    """工作流命令幂等记录。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="commands",
    )
    command_id = models.CharField("命令 ID", max_length=128)
    event = models.CharField("事件", max_length=64)
    payload = models.JSONField("请求体", default=dict)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    response_snapshot = models.JSONField("响应快照", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_command"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "command_id"],
                name="uniq_project_command",
            ),
        ]
        indexes = [
            models.Index(fields=["project", "command_id"]),
        ]


class DramaGenerationJob(models.Model):
    """异步生成任务。"""

    class Status(models.TextChoices):
        PENDING = "pending", "待执行"
        QUEUED = "queued", "已入队"
        RUNNING = "running", "执行中"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"
        DISABLED = "disabled", "已禁用"

    class JobType(models.TextChoices):
        GENERATION = "generation", "生成"
        SCORING = "scoring", "评分"
        COMPLIANCE = "compliance", "合规"
        EXTERNAL_REVIEW = "external_review", "外部审稿"
        PARALLEL_JUDGE = "parallel_judge", "并行评审"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
        null=True,
        blank=True,
    )
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="generation_jobs",
        null=True,
        blank=True,
    )
    job_type = models.CharField("任务类型", max_length=32, choices=JobType.choices)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    request_payload = models.JSONField("请求", default=dict)
    result_payload = models.JSONField("结果", null=True, blank=True)
    progress_events = models.JSONField("进度事件", default=list)
    error_message = models.TextField("错误信息", blank=True, default="")
    celery_task_id = models.CharField("Celery 任务 ID", max_length=64, blank=True, default="")
    command_id = models.CharField("命令 ID", max_length=128, blank=True, default="")
    role = models.CharField("角色", max_length=64, blank=True, default="")
    artifact_key = models.CharField("产物键", max_length=64, blank=True, default="")
    base_revision = models.PositiveIntegerField("执行基线版本", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_generation_job"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["celery_task_id"]),
            models.Index(fields=["project", "command_id"]),
            models.Index(fields=["owner", "command_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project", "command_id"],
                condition=models.Q(command_id__gt=""),
                name="uniq_generation_project_command",
            ),
            models.UniqueConstraint(
                fields=["owner", "command_id"],
                condition=models.Q(project__isnull=True, command_id__gt=""),
                name="uniq_generation_owner_command",
            ),
        ]


class DramaConfigRevision(models.Model):
    """运营配置覆盖不可变历史。"""

    revision = models.PositiveIntegerField("版本号", unique=True)
    overlay = models.JSONField("覆盖内容")
    updated_by = models.CharField("操作人", max_length=128)
    change_reason = models.CharField("变更原因", max_length=500)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_config_revision"
        ordering = ["revision"]


class DramaAuditEvent(models.Model):
    """持久化审计事件。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    actor = models.CharField("操作人", max_length=128)
    action = models.CharField("动作", max_length=64)
    detail = models.JSONField("详情", default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_audit_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["action", "-created_at"]),
        ]


class DramaLlmProvider(models.Model):
    """后台可配置的 OpenAI 兼容 LLM 接入（动态覆盖 .env）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("展示名称", max_length=100)
    base_url = models.CharField("Base URL", max_length=512, blank=True, default="")
    model_name = models.CharField("模型名称", max_length=128, default="gpt-4o-mini")
    api_key_encrypted = models.TextField("加密 API Key", blank=True, default="")
    temperature = models.FloatField("Temperature", default=0.7)
    max_tokens = models.PositiveIntegerField("Max Tokens", default=4096)
    is_enabled = models.BooleanField("启用", default=True)
    is_active = models.BooleanField("当前使用", default=False, db_index=True)
    remark = models.CharField("备注", max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_llm_provider"
        ordering = ["-is_active", "-updated_at"]
        verbose_name = "LLM 接入配置"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return self.name


class V3LlmProviderKey(models.Model):
    """供应商附加 API Key（主 Key 仍在 DramaLlmProvider.api_key_encrypted）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        DramaLlmProvider,
        on_delete=models.CASCADE,
        related_name="extra_keys",
    )
    label = models.CharField("标签", max_length=100)
    api_key_encrypted = models.TextField("加密 API Key", blank=True, default="")
    sort_order = models.PositiveIntegerField("排序", default=0)
    is_enabled = models.BooleanField("启用", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_llm_provider_key"
        ordering = ["sort_order", "created_at"]
        indexes = [
            models.Index(fields=["provider", "sort_order"]),
        ]
        verbose_name = "LLM 附加密钥"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.provider_id}:{self.label}"


class DramaLlmCallLog(models.Model):
    """LLM 调用全链路日志（prompt / response / 耗时 / token）。"""

    class Status(models.TextChoices):
        SUCCESS = "success", "成功"
        ERROR = "error", "失败"

    class Purpose(models.TextChoices):
        ARTIFACT_GENERATION = "artifact_generation", "角色产物生成"
        QUALITY_SCORING = "quality_scoring", "质量评分"
        COMPLIANCE_CHECK = "compliance_check", "合规检查"
        CONNECTIVITY_TEST = "connectivity_test", "连通性测试"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        DramaProject,
        on_delete=models.CASCADE,
        related_name="llm_call_logs",
        null=True,
        blank=True,
    )
    generation_job = models.ForeignKey(
        "DramaGenerationJob",
        on_delete=models.SET_NULL,
        related_name="llm_call_logs",
        null=True,
        blank=True,
    )
    v3_command_run = models.ForeignKey(
        "V3CommandRun",
        on_delete=models.SET_NULL,
        related_name="llm_call_logs",
        null=True,
        blank=True,
    )
    v3_project = models.ForeignKey(
        "V3Project",
        on_delete=models.SET_NULL,
        related_name="llm_call_logs",
        null=True,
        blank=True,
    )
    actor = models.CharField("操作人", max_length=128, default="system")
    role = models.CharField("技能角色", max_length=64, blank=True, default="")
    purpose = models.CharField(
        "调用用途",
        max_length=64,
        choices=Purpose.choices,
        default=Purpose.ARTIFACT_GENERATION,
    )
    seq_in_job = models.PositiveIntegerField("任务内序号", default=0)
    model_name = models.CharField("模型", max_length=128, blank=True, default="")
    base_url = models.CharField("接口地址", max_length=512, blank=True, default="")
    system_prompt = models.TextField("系统提示词", blank=True, default="")
    user_prompt = models.TextField("用户提示词", blank=True, default="")
    response_text = models.TextField("模型回复正文", blank=True, default="")
    response_body = models.JSONField("原始响应", null=True, blank=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=Status.choices,
        default=Status.SUCCESS,
    )
    http_status = models.PositiveIntegerField("HTTP 状态码", null=True, blank=True)
    error_message = models.TextField("错误信息", blank=True, default="")
    latency_ms = models.PositiveIntegerField("耗时(ms)", default=0)
    prompt_tokens = models.PositiveIntegerField("Prompt Tokens", null=True, blank=True)
    cached_prompt_tokens = models.PositiveIntegerField(
        "缓存命中 Prompt Tokens", null=True, blank=True
    )
    completion_tokens = models.PositiveIntegerField("Completion Tokens", null=True, blank=True)
    total_tokens = models.PositiveIntegerField("Total Tokens", null=True, blank=True)
    provider_request_id = models.CharField("厂商 Request ID", max_length=128, blank=True, default="")
    injection_manifest = models.JSONField("注入清单", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_llm_call_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["generation_job", "seq_in_job"]),
            models.Index(fields=["v3_command_run", "-created_at"]),
            models.Index(fields=["v3_project", "-created_at"]),
            models.Index(fields=["role", "-created_at"]),
            models.Index(fields=["status", "-created_at"]),
        ]
        verbose_name = "LLM 调用日志"
        verbose_name_plural = verbose_name

    def __str__(self) -> str:
        return f"{self.role or self.purpose} @ {self.created_at:%Y-%m-%d %H:%M:%S}"


class StudioDecision(models.Model):
    """Human decisions are first-class V6 work items."""
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        ACCEPTED = "accepted", "Accepted"
        DISMISSED = "dismissed", "Dismissed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_decisions")
    title = models.CharField(max_length=240)
    kind = models.CharField(max_length=64, default="quality")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    severity = models.CharField(max_length=16, default="medium")
    context = models.JSONField(default=dict)
    created_by = models.CharField(max_length=128, default="system")
    decided_by = models.CharField(max_length=128, blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["status", "-created_at"]


class StudioChangeSet(models.Model):
    """Candidate edits remain separate from committed artifact versions."""
    class Status(models.TextChoices):
        CANDIDATE = "candidate", "Candidate"
        APPROVED = "approved", "Approved"
        COMMITTED = "committed", "Committed"
        REJECTED = "rejected", "Rejected"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_changesets")
    operation_id = models.CharField(max_length=128)
    base_revision = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CANDIDATE)
    summary = models.CharField(max_length=500, blank=True, default="")
    patch = models.JSONField(default=dict)
    impact = models.JSONField(default=dict)
    created_by = models.CharField(max_length=128, default="system")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class StudioEvidenceLink(models.Model):
    """Links every UI decision to an auditable run, call, or artifact."""
    project = models.ForeignKey(DramaProject, on_delete=models.CASCADE, related_name="studio_evidence")
    decision = models.ForeignKey(StudioDecision, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
    changeset = models.ForeignKey(StudioChangeSet, on_delete=models.CASCADE, null=True, blank=True, related_name="evidence")
    run_id = models.UUIDField(null=True, blank=True)
    call_id = models.UUIDField(null=True, blank=True)
    artifact_key = models.CharField(max_length=128, blank=True, default="")
    label = models.CharField(max_length=240, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)


class StudioExperiment(models.Model):
    """Governance changes are tested against evidence before publication."""
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        RUNNING = "running", "Running"
        READY = "ready", "Ready"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=240)
    hypothesis = models.TextField(blank=True, default="")
    baseline = models.JSONField(default=dict)
    candidate = models.JSONField(default=dict)
    metrics = models.JSONField(default=dict)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    created_by = models.CharField(max_length=128, default="system")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class V3Project(models.Model):
    """V3 产品面项目（与 V6 DramaProject 解耦的最小领域表）。"""

    class EntryType(models.TextChoices):
        ORIGINAL = "original", "原创"
        ADAPT = "adapt", "改编"

    class Stage(models.TextChoices):
        TOPIC = "topic", "选题"
        BLUEPRINT = "blueprint", "蓝图"
        EPISODES = "episodes", "分集"
        WRITING = "writing", "正文"
        QUALITY = "quality", "质检"
        DELIVERY = "delivery", "交付"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="v3_projects",
    )
    title = models.CharField(max_length=200)
    entry_type = models.CharField(max_length=16, choices=EntryType.choices)
    stage = models.CharField(max_length=32, choices=Stage.choices, default=Stage.TOPIC)
    progress_percent = models.PositiveSmallIntegerField(default=0)
    settings = models.JSONField(default=dict, blank=True)
    archived_at = models.DateTimeField(null=True, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_project"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class V3ProjectTemplate(models.Model):
    """V3 自定义项目模板（全局；staff 可写）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    theme_code = models.CharField(max_length=64)
    label_zh = models.CharField(max_length=200)
    dims = models.JSONField(default=dict)
    description = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="v3_project_templates",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_project_template"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.name


class V3CommandRun(models.Model):
    """V3 命令执行记录（异步/幂等追踪）。"""

    class Status(models.TextChoices):
        QUEUED = "queued", "排队"
        RUNNING = "running", "执行中"
        SUCCEEDED = "succeeded", "成功"
        FAILED = "failed", "失败"
        UNSUPPORTED = "unsupported", "本阶段未实现"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="v3_command_runs",
    )
    project = models.ForeignKey(
        V3Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="command_runs",
    )
    command_type = models.CharField(max_length=64)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.QUEUED)
    idempotency_key = models.CharField(max_length=64, blank=True, default="")
    request_payload = models.JSONField(default=dict)
    result_payload = models.JSONField(default=dict)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_command_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["owner", "-created_at"]),
            models.Index(fields=["command_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.command_type} ({self.status})"


class V3ArtifactVersion(models.Model):
    """V3 产物版本（draft / candidate / committed / superseded）。"""

    class Status(models.TextChoices):
        DRAFT = "draft", "草稿"
        CANDIDATE = "candidate", "候选"
        COMMITTED = "committed", "已确认"
        SUPERSEDED = "superseded", "已替代"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        V3Project,
        on_delete=models.CASCADE,
        related_name="artifacts",
    )
    artifact_key = models.CharField(max_length=64)
    version = models.PositiveIntegerField()
    schema_version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=16, choices=Status.choices)
    payload = models.JSONField(default=dict)
    command_run = models.ForeignKey(
        V3CommandRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="artifacts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_artifact_version"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "artifact_key", "version"],
                name="uniq_v3_artifact_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.artifact_key} v{self.version} ({self.status})"


class V3ScriptDraft(models.Model):
    """V3 正文人工草稿（按集号，与 AI episode_scripts 候选分离）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        V3Project,
        on_delete=models.CASCADE,
        related_name="script_drafts",
    )
    episode_number = models.PositiveIntegerField()
    payload = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_script_draft"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "episode_number"],
                name="uniq_v3_project_episode_script_draft",
            ),
        ]

    def __str__(self) -> str:
        return f"ep{self.episode_number} draft ({self.project_id})"


class V3QualityFinding(models.Model):
    """V3 质检/合规问题（可接受、可追踪处理状态）。"""

    class Source(models.TextChoices):
        QUALITY = "quality", "质量"
        COMPLIANCE = "compliance", "合规"

    class Status(models.TextChoices):
        OPEN = "open", "待处理"
        ACCEPTED = "accepted", "已接受"
        RESOLVED = "resolved", "已解决"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        V3Project,
        on_delete=models.CASCADE,
        related_name="quality_findings",
    )
    source = models.CharField(max_length=16, choices=Source.choices)
    finding_key = models.CharField(max_length=128)  # 稳定键：如 defect index 或 hash
    title = models.CharField(max_length=256)
    severity = models.CharField(max_length=32, blank=True, default="")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.OPEN)
    report_artifact = models.ForeignKey(
        V3ArtifactVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_quality_finding"
        constraints = [
            models.UniqueConstraint(
                fields=["project", "source", "finding_key"],
                name="uniq_v3_finding_project_source_key",
            )
        ]

    def __str__(self) -> str:
        return f"{self.source}:{self.finding_key} ({self.status})"


class V3SystemConfigRevision(models.Model):
    """V3 全局系统配置不可变修订（overlay 叠 foundation presets）。"""

    revision = models.PositiveIntegerField(unique=True)
    overlay = models.JSONField(default=dict)
    updated_by = models.CharField(max_length=128)
    change_reason = models.CharField(max_length=500, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_system_config_revision"
        ordering = ["-revision"]

    def __str__(self) -> str:
        return f"system_config r{self.revision}"


class V3RoleModelMapping(models.Model):
    """V3 技能角色 → LLM Provider 映射（无映射时运行时用 active provider）。"""

    role_key = models.CharField(max_length=64, unique=True)
    provider = models.ForeignKey(
        DramaLlmProvider,
        on_delete=models.CASCADE,
        related_name="role_mappings",
    )
    temperature = models.FloatField(null=True, blank=True)
    max_tokens = models.PositiveIntegerField(null=True, blank=True)
    backup_provider_ids = models.JSONField(default=list, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_role_model_mapping"

    def __str__(self) -> str:
        return self.role_key


class V3FailoverAttempt(models.Model):
    """V3 LLM 主备链单次切换尝试审计。"""

    class Status(models.TextChoices):
        SUCCEEDED = "succeeded", "成功"
        FAILED_SWITCHABLE = "failed_switchable", "可切换失败"
        FAILED_TERMINAL = "failed_terminal", "终态失败"
        SKIPPED = "skipped", "跳过"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    v3_command_run = models.ForeignKey(
        V3CommandRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="failover_attempts",
    )
    v3_project = models.ForeignKey(
        V3Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="failover_attempts",
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="v3_failover_attempts",
    )
    role_key = models.CharField(max_length=64)
    provider = models.ForeignKey(
        DramaLlmProvider,
        on_delete=models.CASCADE,
        related_name="failover_attempts",
    )
    attempt_index = models.PositiveIntegerField()
    status = models.CharField(max_length=32, choices=Status.choices)
    error_code = models.CharField(max_length=64, blank=True, default="")
    error_message = models.TextField(blank=True, default="")
    llm_call_log = models.ForeignKey(
        DramaLlmCallLog,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="failover_attempts",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "drama_v3_failover_attempt"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["v3_command_run", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.role_key}#{self.attempt_index} ({self.status})"


class V3ModelPrice(models.Model):
    """V3 LLM 模型单价（按 provider + model_name）。"""

    provider = models.ForeignKey(
        DramaLlmProvider,
        on_delete=models.CASCADE,
        related_name="model_prices",
    )
    model_name = models.CharField(max_length=128)
    price_in_per_1k = models.DecimalField(max_digits=16, decimal_places=6)
    price_out_per_1k = models.DecimalField(max_digits=16, decimal_places=6)
    price_cache_in_per_1k = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="缓存命中输入单价；空则按输入单价计",
    )
    currency = models.CharField(max_length=8, default="CNY")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_model_price"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "model_name"],
                name="uniq_v3_model_price_provider_model",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.provider_id}:{self.model_name} ({self.currency})"


class V3UsageDailyRollup(models.Model):
    """V3 LLM 用量按日物化汇总（Asia/Shanghai 日历日）。"""

    date = models.DateField()
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="v3_usage_daily_rollups",
    )
    project = models.ForeignKey(
        V3Project,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="usage_daily_rollups",
    )
    command_type = models.CharField(max_length=64, null=True, blank=True)
    model_name = models.CharField(max_length=128)
    provider = models.ForeignKey(
        DramaLlmProvider,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="usage_daily_rollups",
    )
    prompt_tokens = models.BigIntegerField(default=0)
    cached_prompt_tokens = models.BigIntegerField(default=0)
    completion_tokens = models.BigIntegerField(default=0)
    total_tokens = models.BigIntegerField(default=0)
    call_count = models.PositiveIntegerField(default=0)
    success_count = models.PositiveIntegerField(default=0)
    estimated_cost = models.DecimalField(
        max_digits=16, decimal_places=6, default=0
    )
    unpriced_call_count = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "drama_v3_usage_daily_rollup"
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "date",
                    "owner",
                    "project",
                    "command_type",
                    "model_name",
                    "provider",
                ],
                name="uniq_v3_usage_daily_rollup_dims",
                nulls_distinct=False,
            ),
        ]

    def __str__(self) -> str:
        return f"{self.date} owner={self.owner_id} model={self.model_name}"


class ScriptReview(models.Model):
    """独立剧本评审件（外界剧本，与项目主链解耦）。"""

    class SourceType(models.TextChoices):
        PASTE = "paste", "粘贴"
        UPLOAD = "upload", "上传"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="script_reviews",
    )
    project = models.ForeignKey(
        V3Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="script_reviews",
    )
    title = models.CharField(max_length=200)
    source_type = models.CharField(max_length=16, choices=SourceType.choices)
    source_filename = models.CharField(max_length=255, blank=True, default="")
    script_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_script_review"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["owner", "-updated_at"]),
        ]

    def __str__(self) -> str:
        return self.title


class ScriptReviewRun(models.Model):
    """单次评审执行记录（质量评分 / 合规审查）。"""

    class Kind(models.TextChoices):
        QUALITY = "quality", "质量评分"
        COMPLIANCE = "compliance", "合规审查"

    class Status(models.TextChoices):
        QUEUED = "queued", "排队"
        RUNNING = "running", "执行中"
        SUCCEEDED = "succeeded", "成功"
        FAILED = "failed", "失败"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(
        ScriptReview,
        on_delete=models.CASCADE,
        related_name="runs",
    )
    kind = models.CharField(max_length=16, choices=Kind.choices)
    status = models.CharField(
        max_length=32, choices=Status.choices, default=Status.QUEUED
    )
    command_run = models.ForeignKey(
        V3CommandRun,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="script_review_runs",
    )
    report_payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "drama_script_review_run"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["review", "kind", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.kind}:{self.status}"
