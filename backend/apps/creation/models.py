# -*- coding: utf-8 -*-
"""
创作模块数据模型

核心表：
1. Project - 创作项目（对应一次创作请求产生的完整剧本）
2. ProjectFusionArtifact / AgentExecutionRun - 独立 Agent 产物与执行记录
3. ScriptWork - 剧本作品文件（存储二进制文件路径，含数字水印）
4. ShareLink - 分享链接（一次性 token，过期自动失效）

关键安全设计：
- script_data / rendered_html 等原始创作数据绝不直接暴露给前端
- ScriptWork.storage_path 为加密路径，访问时需经服务层鉴权
- ShareLink.token 为一次性随机字符串，用于作品分享溯源
"""

import uuid
import secrets

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone


# ============================================================
# Project - 创作项目
# ============================================================
class Project(models.Model):
    """创作项目

    每调用一次创作接口创建一个 Project，包含创作参数 + 状态 +
    生成的作品关联。
    """

    # 项目状态枚举
    STATUS_PENDING = "pending"      # 排队中
    STATUS_RUNNING = "running"      # 创作中
    STATUS_AWAITING = "awaiting"    # 分步模式：等待用户确认
    STATUS_COMPLETED = "completed"  # 完成
    STATUS_FAILED = "failed"        # 失败

    STATUS_CHOICES = [
        (STATUS_PENDING, "排队中"),
        (STATUS_RUNNING, "创作中"),
        (STATUS_AWAITING, "待确认"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
    ]

    MODE_AUTO = "auto"
    MODE_STEP = "step"
    MODE_WORKSPACE = "workspace"
    PIPELINE_MODE_CHOICES = [
        (MODE_AUTO, "一键生成"),
        (MODE_STEP, "分步掌控"),
        (MODE_WORKSPACE, "技能工作台"),
    ]

    # 输出格式变体（默认 B）
    FORMAT_A = "A"
    FORMAT_B = "B"
    FORMAT_C = "C"
    FORMAT_D = "D"
    FORMAT_CHOICES = [
        (FORMAT_A, "变体 A"),
        (FORMAT_B, "变体 B"),
        (FORMAT_C, "变体 C"),
        (FORMAT_D, "变体 D"),
    ]

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        verbose_name="项目ID",
    )

    # 创作请求参数（完整保留，用于后台追溯）
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects",
        verbose_name="所属用户",
        help_text="该创作归属的会员用户",
    )
    theme = models.CharField(
        "题材", max_length=128, help_text="如 family-revenge / overbearing-ceo / matrix_key"
    )
    core_idea = models.TextField(
        "核心创意", help_text="一句话核心创意，用于生成剧本框架"
    )
    episode_count = models.IntegerField("集数", default=30)
    format_variant = models.CharField(
        "输出格式变体",
        max_length=2,
        choices=FORMAT_CHOICES,
        default=FORMAT_B,
    )
    audience = models.CharField(
        "目标受众", max_length=200, blank=True, default=""
    )
    reference_work = models.CharField(
        "参考作品", max_length=2000, blank=True, default=""
    )
    novel_text = models.TextField(
        "小说原文",
        blank=True,
        default="",
        help_text="小说改编入口提交的完整原文，供 adapt Agent 使用",
    )
    # project-brief.schema 对齐字段
    target_platform = models.CharField(
        "目标平台", max_length=32, blank=True, default="douyin",
        help_text="douyin / kuaishou / wechat / multi",
    )
    episode_duration_minutes = models.FloatField(
        "单集时长(分钟)", default=2.0,
    )
    creation_entry = models.CharField(
        "创作入口", max_length=32, blank=True, default="from-scratch",
        help_text="from-scratch / from-outline / from-reference / ip-sequel / novel-adaptation",
    )
    budget_level = models.CharField(
        "预算档位", max_length=16, blank=True, default="medium",
        help_text="low / medium / high",
    )
    global_market = models.CharField(
        "市场范围", max_length=16, blank=True, default="domestic",
    )

    # 会员消费记录（用于后续统计）
    user_membership = models.ForeignKey(
        "membership.UserMembership",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="消耗的会员",
    )

    # 状态 & 流程进度（执行态由 project_execution + Drama SSOT 推导）
    pipeline_mode = models.CharField(
        "流水线模式",
        max_length=16,
        choices=PIPELINE_MODE_CHOICES,
        default=MODE_WORKSPACE,
        help_text="workspace=按技能模块；auto=一键跑完；step=每节点暂停待确认",
    )
    progress_percent = models.IntegerField("进度百分比", default=0)
    error_message = models.TextField(
        "错误信息", blank=True, default="", help_text="status=failed 时填充"
    )
    overall_score = models.FloatField("8维综合分", null=True, blank=True)
    grade = models.CharField("报告等级", max_length=16, blank=True, default="")
    ready_at = models.DateTimeField("可发布时间", null=True, blank=True)
    skill_version = models.CharField(
        "技能版本", max_length=32, blank=True, default="",
        help_text="来自历史 project-config projectMeta.version",
    )
    compliance_tier = models.CharField(
        "合规分层", max_length=32, blank=True, default="domestic",
        help_text="domestic | ai-comic | global-*",
    )

    # 跨集连续性档案（来自 drama-continuity-recorder Skill）
    character_continuity_state = models.JSONField(
        "连续性档案",
        default=dict,
        blank=True,
        help_text=(
            "由 drama-continuity-recorder 维护的人设/事件连续性档案。"
            "结构见 drama-continuity-recorder/SKILL.md#character-states.json。"
            "前端工作台用于展示跨集一致性概览，不直接用于创作逻辑。"
        ),
    )
    agent_notes = models.JSONField(
        "Agent 项目记忆",
        default=dict,
        blank=True,
        help_text="跨 Agent 的用户偏好与拒绝项，如 rejects / style_preferences / character_guidance",
    )

    # 安全/展示用缓存字段（不直接返回给前端，由服务层按需使用）
    title = models.CharField(
        "剧本标题", max_length=200, blank=True, default="",
        help_text="仅后台展示与作品列表使用",
    )
    total_duration_minutes = models.IntegerField(
        "预计总时长(分钟)", default=0
    )

    # 预渲染 HTML（由服务层写入，用于前端直接展示剧本内容）
    rendered_progress_html = models.TextField(
        "预渲染进度 HTML", blank=True, default="",
        help_text="由 services 层生成，前端直接插入 DOM",
    )
    rendered_result_html = models.TextField(
        "预渲染结果 HTML", blank=True, default="",
        help_text="完成时生成，含数字水印，前端直接展示",
    )

    created_at = models.DateTimeField("创建时间", default=timezone.now)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    completed_at = models.DateTimeField(
        "完成时间", null=True, blank=True
    )

    # ── 【运营 M2】内容质量统计字段 ─────────────────────────────
    # 用于运营 Dashboard：保存率/导出率/弃用率核心指标
    user_edit_count = models.PositiveIntegerField(
        "用户编辑次数", default=0,
        help_text="用户在工作台内对 Project 的手动编辑次数（保存草稿节点+1）",
    )
    final_export_count = models.PositiveIntegerField(
        "最终导出次数", default=0,
        help_text="用户从工作台成功下载/导出最终剧本的次数",
    )
    last_edited_at = models.DateTimeField(
        "最近编辑时间", null=True, blank=True,
        help_text="用户最近一次编辑时间；超过 7 天未编辑+未完成=潜在弃用",
    )
    abandoned_at = models.DateTimeField(
        "弃用时间", null=True, blank=True, db_index=True,
        help_text="用户主动放弃或超过 7 天未活跃即视为弃用；用于运营漏斗/质量分析",
    )
    is_quality_sampled = models.BooleanField(
        "已采样分析", default=False, db_index=True,
        help_text="运营分析/反馈抽样的标记位，避免重复抽样",
    )

    # ── Drama 工作台扩展（原 drama_project 表，合并至单表）────────────────
    track_mode = models.CharField(
        "创作轨道",
        max_length=16,
        blank=True,
        default="",
        help_text="fast / expert；空表示非 Drama 工作台项目",
    )
    drama_stage = models.CharField(
        "Drama 当前阶段",
        max_length=32,
        blank=True,
        default="strategy",
        help_text="Drama 工作台阶段代码",
    )
    completed_roles = models.JSONField(
        "已完成 Drama 角色",
        default=list,
        blank=True,
    )
    word_count_stats = models.JSONField(
        "分集字数统计",
        default=dict,
        blank=True,
    )
    quality_scores = models.JSONField(
        "Drama 8维评分",
        default=dict,
        blank=True,
    )
    delivery_status = models.CharField(
        "交付状态",
        max_length=16,
        blank=True,
        default="pending",
        help_text="pending / ready / delivered",
    )
    total_tokens_used = models.IntegerField(
        "累计 Token 消耗",
        default=0,
    )
    total_cost_cents = models.IntegerField(
        "累计费用（分）",
        default=0,
    )

    class Meta:
        verbose_name = "创作项目"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["abandoned_at"]),
            models.Index(fields=["-created_at"]),
        ]

    @property
    def execution_status(self) -> str:
        from .project_execution import derive_execution_status

        return derive_execution_status(self)

    def get_status_display(self) -> str:
        return dict(self.STATUS_CHOICES).get(self.execution_status, self.execution_status or "—")

    @property
    def is_drama_workspace(self) -> bool:
        from apps.drama.constants import DramaTrackMode

        return self.track_mode in (DramaTrackMode.FAST, DramaTrackMode.EXPERT)

    def get_completion_rate(self) -> float:
        """Drama 工作台完成率（按轨道有效角色计，封顶 100%）。"""
        if not self.is_drama_workspace:
            return float(min(100, max(0, self.progress_percent or 0)))
        from apps.drama.progress_service import DramaProgressService

        track_roles = DramaProgressService.list_track_agent_ids(self)
        if not track_roles:
            from apps.creation.agent_runtime.entry_plan import DramaEntryPlan

            track_roles = DramaEntryPlan.list_agent_ids(track_mode=self.track_mode or "fast")

        expected = set(track_roles)
        completed = set(self.completed_roles or []) & expected
        total = len(expected)
        if total <= 0:
            return 0.0
        return round(min(100.0, len(completed) / total * 100), 1)

    def normalized_completed_roles(self) -> list[str]:
        """仅保留当前轨道内的已完成角色。"""
        if not self.is_drama_workspace:
            return list(self.completed_roles or [])
        from apps.drama.progress_service import DramaProgressService

        allowed = set(DramaProgressService.list_track_agent_ids(self))
        if not allowed:
            return list(dict.fromkeys(self.completed_roles or []))
        return [rid for rid in (self.completed_roles or []) if rid in allowed]

    def get_drama_stage_display(self) -> str:
        from apps.drama.constants import DramaStage

        for value, label in DramaStage.choices:
            if value == self.drama_stage:
                return label
        return self.drama_stage or ""

    def get_track_mode_display(self) -> str:
        from apps.drama.constants import DramaTrackMode

        for value, label in DramaTrackMode.choices:
            if value == self.track_mode:
                return label
        return self.track_mode or ""

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.id.hex[:8]} - {self.theme}"


# ============================================================
# ScriptWork - 剧本作品文件
# ============================================================
class ScriptWork(models.Model):
    """剧本作品文件

    一个 Project 可能生成多种格式的作品文件（Markdown / HTML / ZIP 等）。
    所有原始文件存储在加密路径，由服务层统一处理下载。
    """

    FORMAT_MARKDOWN = "md"
    FORMAT_HTML = "html"
    FORMAT_ZIP = "zip"
    FORMAT_PDF = "pdf"

    FORMAT_CHOICES = [
        (FORMAT_MARKDOWN, "Markdown"),
        (FORMAT_HTML, "HTML"),
        (FORMAT_ZIP, "ZIP 打包"),
        (FORMAT_PDF, "PDF"),
    ]

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        verbose_name="作品文件ID",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="works",
        verbose_name="所属项目",
    )

    file_format = models.CharField(
        "文件格式", max_length=8, choices=FORMAT_CHOICES, default=FORMAT_MARKDOWN
    )
    storage_path = models.CharField(
        "加密存储路径", max_length=500,
        help_text="不直接暴露给前端，由服务层鉴权后访问",
    )
    file_name = models.CharField(
        "原始文件名", max_length=255,
        help_text="下载时展示给用户",
    )
    size_bytes = models.IntegerField("文件大小(字节)", default=0)

    # 数字水印 token：用于下载文件的溯源，不可修改
    watermark_token = models.CharField(
        "数字水印 token", max_length=64, unique=True,
        help_text="含 user_id + project_id + timestamp 信息，用于溯源",
    )

    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "剧本作品文件"
        verbose_name_plural = verbose_name
        ordering = ["project_id", "-created_at"]
        indexes = [
            models.Index(fields=["project_id"]),
            models.Index(fields=["watermark_token"]),
        ]

    def __str__(self) -> str:
        return f"{self.project.id.hex[:8]} - {self.file_name}"


# ============================================================
# ShareLink - 分享链接
# ============================================================
class ShareLink(models.Model):
    """分享链接

    为某个作品生成一个可对外分享的一次性 token。
    token 有效期默认 7 天，访问次数有上限。
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        verbose_name="分享ID",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="share_links",
        verbose_name="所属项目",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="share_links",
        verbose_name="创建者",
    )

    token = models.CharField(
        "分享 token", max_length=64, unique=True,
        help_text="一次性随机字符串，公开可访问",
    )

    # 权限与生命周期
    view_limit = models.IntegerField("最大查看次数", default=100)
    view_count = models.IntegerField("已查看次数", default=0)
    expires_at = models.DateTimeField("过期时间")

    # 分享配置
    allow_download = models.BooleanField("允许下载", default=False)
    custom_title = models.CharField(
        "自定义标题", max_length=200, blank=True, default=""
    )

    is_active = models.BooleanField("是否有效", default=True)
    created_at = models.DateTimeField("创建时间", default=timezone.now)
    last_viewed_at = models.DateTimeField("最后查看时间", null=True, blank=True)

    class Meta:
        verbose_name = "分享链接"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"share-{self.token[:8]} ({self.project.id.hex[:8]})"

    @property
    def is_expired(self) -> bool:
        if self.expires_at and timezone.now() > self.expires_at:
            return True
        return False

    @property
    def is_available(self) -> bool:
        return (
            self.is_active
            and not self.is_expired
            and (self.view_limit <= 0 or self.view_count < self.view_limit)
        )

    def record_view(self) -> None:
        self.view_count += 1
        self.last_viewed_at = timezone.now()
        # 超过查看次数则自动失效
        if self.view_limit > 0 and self.view_count >= self.view_limit:
            self.is_active = False
        self.save(update_fields=["view_count", "last_viewed_at", "is_active"])

    @classmethod
    def generate_token(cls) -> str:
        """生成安全的分享 token"""
        return secrets.token_urlsafe(32)


# ============================================================
# DownloadToken - 一次性下载 token
# ============================================================
class DownloadToken(models.Model):
    """一次性下载 token

    用于 /api/creation/download/<token>/ 接口的短时效下载凭证。
    有效期极短（默认 15 分钟），使用后立即失效。
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="download_tokens",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="download_tokens",
    )

    token = models.CharField(max_length=64, unique=True)
    file_format = models.CharField(max_length=8, default="md")
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "下载 token"
        verbose_name_plural = verbose_name
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self) -> str:
        return f"dl-{self.token[:8]}"

    @property
    def is_valid(self) -> bool:
        if self.is_used:
            return False
        return timezone.now() <= self.expires_at

    def mark_used(self) -> None:
        self.is_used = True
        self.used_at = timezone.now()
        self.save(update_fields=["is_used", "used_at"])

    @classmethod
    def generate_token(cls) -> str:
        return secrets.token_urlsafe(24)


# ============================================================
# ProjectFusionArtifact - 融合 Schema 产物（JSONB）
# ============================================================
class ProjectFusionArtifact(models.Model):
    """按 fusion-plan §6.6 存储节点产物，网站为唯一持久化层。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="fusion_artifacts",
    )
    artifact_key = models.CharField(
        "产物键",
        max_length=64,
        help_text="project_brief / gate_full / script_score_report 等",
    )
    payload = models.JSONField("JSON 载荷", default=dict)
    version = models.IntegerField("版本", default=1)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "融合产物"
        verbose_name_plural = verbose_name
        unique_together = [["project", "artifact_key"]]
        indexes = [
            models.Index(fields=["project", "artifact_key"]),
        ]

    def __str__(self) -> str:
        return f"{self.project_id} · {self.artifact_key}"


# ============================================================
# AgentExecutionRun - 独立 Agent 执行记录
# ============================================================
class AgentExecutionRun(models.Model):
    """单次 Agent（主链节点）执行记录。"""

    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_PARTIAL = "partial"

    STATUS_CHOICES = [
        (STATUS_RUNNING, "执行中"),
        (STATUS_COMPLETED, "成功"),
        (STATUS_FAILED, "失败"),
        (STATUS_PARTIAL, "部分成功"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="agent_execution_runs",
        verbose_name="项目",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_execution_runs",
        verbose_name="用户",
    )
    agent_id = models.CharField("Agent ID", max_length=64, db_index=True)
    node_index = models.PositiveSmallIntegerField("节点序号", null=True, blank=True, db_index=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_RUNNING,
        db_index=True,
    )
    batch_from = models.PositiveIntegerField("批次起始", null=True, blank=True)
    batch_to = models.PositiveIntegerField("批次结束", null=True, blank=True)
    outline_mode = models.CharField("大纲模式", max_length=32, blank=True, default="")
    input_summary = models.JSONField("输入摘要", default=dict, blank=True)
    output_summary = models.JSONField("输出摘要", default=dict, blank=True)
    output_artifact_key = models.CharField("产出键", max_length=64, blank=True, default="")
    agent_version = models.CharField("Agent 版本", max_length=32, blank=True, default="")
    prompt_version = models.CharField("Prompt 版本", max_length=32, blank=True, default="")
    input_artifact_keys = models.JSONField("输入产物键", default=list, blank=True)
    output_artifact_keys = models.JSONField("输出产物键", default=list, blank=True)
    input_snapshot = models.JSONField("输入快照", default=dict, blank=True)
    rendered_prompt_preview = models.TextField("Prompt 预览", blank=True, default="")
    prompt_tokens = models.PositiveIntegerField("Prompt Tokens", null=True, blank=True)
    completion_tokens = models.PositiveIntegerField("Completion Tokens", null=True, blank=True)
    total_tokens = models.PositiveIntegerField("Total Tokens", null=True, blank=True)
    estimated_prompt_tokens = models.PositiveIntegerField("预估 Prompt Tokens", null=True, blank=True)
    model_name = models.CharField("模型", max_length=128, blank=True, default="")
    provider_name = models.CharField("Provider", max_length=128, blank=True, default="")
    started_by = models.CharField("触发方", max_length=16, blank=True, default="user")
    run_params = models.JSONField("运行参数", default=dict, blank=True)
    overwrite_mode = models.CharField("覆盖模式", max_length=16, blank=True, default="replace")
    error_message = models.TextField("错误信息", blank=True, default="")
    started_at = models.DateTimeField("开始时间", default=timezone.now, db_index=True)
    finished_at = models.DateTimeField("结束时间", null=True, blank=True)

    class Meta:
        db_table = "creation_agent_execution_run"
        verbose_name = "Agent 执行记录"
        verbose_name_plural = verbose_name
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["project", "-started_at"]),
            models.Index(fields=["agent_id", "-started_at"]),
            models.Index(fields=["project", "status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["project"],
                condition=Q(status="running"),
                name="uniq_running_agent_per_project",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.agent_id} node={self.node_index} {self.status}"


# ============================================================
# ProjectChunk - 流式生成分片（单集/单条）
# ============================================================
class ProjectChunk(models.Model):
    """流式 Agent 产出分片；index 为集号/序号（DB 权威）。"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="chunks",
        verbose_name="项目",
    )
    kind = models.CharField("分片类型", max_length=32, db_index=True)
    index = models.PositiveIntegerField("序号/集号", db_index=True)
    data = models.JSONField("分片数据", default=dict, blank=True)
    run = models.ForeignKey(
        AgentExecutionRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="chunks",
        verbose_name="执行记录",
    )
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "creation_project_chunk"
        verbose_name = "项目分片"
        verbose_name_plural = verbose_name
        ordering = ["index"]
        unique_together = [["project", "kind", "index"]]
        indexes = [
            models.Index(fields=["project", "kind", "index"]),
        ]

    def __str__(self) -> str:
        return f"{self.project_id} · {self.kind}[{self.index}]"


# ============================================================
# SkillGenerationLog - 流式/技能生成追踪
# ============================================================
class SkillGenerationLog(models.Model):
    """流式生成完成/失败日志（trace 维度）。"""

    STATUS_OK = "ok"
    STATUS_ERROR = "error"
    STATUS_TRUNCATED = "truncated"
    STATUS_CHOICES = [
        (STATUS_OK, "成功"),
        (STATUS_ERROR, "失败"),
        (STATUS_TRUNCATED, "截断"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    trace_id = models.CharField("追踪 ID", max_length=64, db_index=True)
    skill_id = models.CharField("技能 ID", max_length=64, blank=True, default="", db_index=True)
    agent_id = models.CharField("Agent ID", max_length=64, blank=True, default="", db_index=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skill_generation_logs",
        verbose_name="用户",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skill_generation_logs",
        verbose_name="项目",
    )
    run = models.ForeignKey(
        AgentExecutionRun,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="generation_logs",
        verbose_name="执行记录",
    )
    prompt_tokens = models.PositiveIntegerField("Prompt Tokens", null=True, blank=True)
    completion_tokens = models.PositiveIntegerField("Completion Tokens", null=True, blank=True)
    total_tokens = models.PositiveIntegerField("Total Tokens", null=True, blank=True)
    provider = models.CharField("Provider", max_length=128, blank=True, default="")
    model = models.CharField("模型", max_length=128, blank=True, default="")
    duration_ms = models.PositiveIntegerField("耗时(ms)", null=True, blank=True)
    status = models.CharField(
        "状态",
        max_length=16,
        choices=STATUS_CHOICES,
        default=STATUS_OK,
        db_index=True,
    )
    error_message = models.TextField("错误信息", blank=True, default="")
    created_at = models.DateTimeField("创建时间", auto_now_add=True, db_index=True)

    class Meta:
        db_table = "creation_skill_generation_log"
        verbose_name = "技能生成日志"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "-created_at"]),
            models.Index(fields=["trace_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.trace_id} {self.agent_id or self.skill_id} {self.status}"


# ============================================================
# ScriptQualityDefect：剧本质量缺陷记录
# ============================================================
class ScriptQualityDimension(models.TextChoices):
    """剧本质量维度 — 与 ScriptQualityDefect.dimension 及规则进化分析对齐。"""

    HOOK = "hook", "钩子/开场"
    EMOTION = "emotion", "情绪设计"
    REVERSAL = "reversal", "反转"
    STRUCTURE = "structure", "结构节奏"
    COMPLIANCE = "compliance", "合规"


class ScriptQualityDefect(models.Model):
    """剧本质量缺陷

    由质检 Agent 自动写入，或人工标注。
    与 Project 关联，记录哪集哪个维度存在何种问题。

    dimension 维度：
    - hook       : 钩子/开场
    - emotion    : 情绪设计（QDN）
    - reversal   : 反转
    - structure  : 结构节奏
    - compliance : 合规
    """

    SOURCE_AUTO   = "auto"
    SOURCE_MANUAL = "manual"

    SOURCE_CHOICES = [
        (SOURCE_AUTO,   "自动检测"),
        (SOURCE_MANUAL, "人工标注"),
    ]

    STATUS_OPEN     = "open"
    STATUS_RESOLVED = "resolved"

    STATUS_CHOICES = [
        (STATUS_OPEN,     "待处理"),
        (STATUS_RESOLVED, "已处理"),
    ]

    project     = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name="quality_defects", verbose_name="所属项目",
    )
    episode     = models.IntegerField("集数", null=True, blank=True,
                                      help_text="具体集数；null 表示整体性问题")
    dimension   = models.CharField("质量维度", max_length=50, db_index=True,
                                   choices=ScriptQualityDimension.choices,
                                   help_text="hook/emotion/reversal/structure/compliance")
    defect_type = models.CharField("缺陷类型", max_length=100,
                                   help_text="如 hook_too_weak / qdn_mismatch / paywall_missing")
    score       = models.FloatField("得分", null=True, blank=True,
                                    help_text="该维度得分（0-100），null 表示未评分")
    details     = models.JSONField("详细信息", default=dict, blank=True,
                                   help_text="自由结构，如 { threshold: 75, actual: 62, suggestion: '...' }")
    source      = models.CharField("来源", max_length=20,
                                   choices=SOURCE_CHOICES, default=SOURCE_AUTO, db_index=True)
    status      = models.CharField("状态", max_length=20,
                                   choices=STATUS_CHOICES, default=STATUS_OPEN, db_index=True)
    created_at  = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        db_table = "creation_script_quality_defect"
        verbose_name = "剧本质量缺陷"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"], name="sqd_project_status_idx"),
            models.Index(fields=["dimension", "defect_type"], name="sqd_dimension_idx"),
        ]

    def __str__(self) -> str:
        ep = f" E{self.episode:02d}" if self.episode else ""
        return f"{self.project_id.hex[:8]}{ep} [{self.dimension}] {self.defect_type}"
