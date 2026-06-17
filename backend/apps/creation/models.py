"""
创作模块数据模型

核心表：
1. Project - 创作项目（对应一次创作请求产生的完整剧本）
2. CreationNode - 创作节点（7 节点流水线的每个节点记录）
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

    FUSION_DRAFT = "draft"
    FUSION_PLANNING = "planning"
    FUSION_WRITING = "writing"
    FUSION_REVIEWING = "reviewing"
    FUSION_SCORING = "scoring"
    FUSION_READY = "ready"
    FUSION_BLOCKED = "blocked"

    FUSION_STATUS_CHOICES = [
        (FUSION_DRAFT, "立项中"),
        (FUSION_PLANNING, "策划中"),
        (FUSION_WRITING, "创作中"),
        (FUSION_REVIEWING, "质检中"),
        (FUSION_SCORING, "评分中"),
        (FUSION_READY, "可发布"),
        (FUSION_BLOCKED, "需修改"),
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
        "题材", max_length=64, help_text="如 family-revenge / overbearing-ceo"
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

    # 状态 & 流程进度
    status = models.CharField(
        "状态", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    pipeline_mode = models.CharField(
        "流水线模式",
        max_length=16,
        choices=PIPELINE_MODE_CHOICES,
        default=MODE_WORKSPACE,
        help_text="workspace=按技能模块；auto=一键跑完；step=每节点暂停待确认",
    )
    pipeline_pack = models.ForeignKey(
        "workflow.FusionPipelinePack",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name="流水线模板",
    )
    current_node_index = models.IntegerField(
        "当前节点索引", default=0, help_text="0 表示未开始，1-7 表示正在/已完成该节点"
    )
    total_nodes = models.IntegerField("总节点数", default=7)
    progress_percent = models.IntegerField("进度百分比", default=0)
    error_message = models.TextField(
        "错误信息", blank=True, default="", help_text="status=failed 时填充"
    )

    # 融合技能状态（SSOT：fusion-plan §5；与 legacy status 并存）
    fusion_status = models.CharField(
        "融合流程状态",
        max_length=16,
        choices=FUSION_STATUS_CHOICES,
        blank=True,
        default="",
    )
    overall_score = models.FloatField("8维综合分", null=True, blank=True)
    grade = models.CharField("报告等级", max_length=16, blank=True, default="")
    ready_at = models.DateTimeField("可发布时间", null=True, blank=True)
    skill_version = models.CharField(
        "技能版本", max_length=32, blank=True, default="",
        help_text="来自 demo4book project-config projectMeta.version",
    )
    # 新增：记录创作命中了哪个工作流版本（用于灰度追踪）
    gray_flow_version = models.CharField(
        "命中工作流版本", max_length=64, blank=True, default="",
        help_text="记录创作请求命中的工作流 pack version，用于灰度流量分析",
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

    class Meta:
        verbose_name = "创作项目"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["abandoned_at", "status"]),
            models.Index(fields=["-created_at", "status"]),
        ]

    def save(self, *args, **kwargs):
        """保存时自动将 fusion_status 同步到 status 字段（统一状态机过渡方案）"""
        if self.fusion_status:
            self.status = self._derive_status_from_fusion()
        super().save(*args, **kwargs)

    def _derive_status_from_fusion(self) -> str:
        """根据 fusion_status 派生 legacy status 字段值"""
        mapping = {
            self.FUSION_DRAFT:     self.STATUS_PENDING,
            self.FUSION_PLANNING:  self.STATUS_RUNNING,
            self.FUSION_WRITING:   self.STATUS_RUNNING,
            self.FUSION_REVIEWING: self.STATUS_RUNNING,
            self.FUSION_SCORING:   self.STATUS_RUNNING,
            self.FUSION_READY:     self.STATUS_COMPLETED,
            self.FUSION_BLOCKED:   self.STATUS_FAILED,
        }
        return mapping.get(self.fusion_status, self.status)

    def __str__(self) -> str:
        return f"[{self.get_status_display()}] {self.id.hex[:8]} - {self.theme}"


# ============================================================
# CreationNode - 创作节点记录
# ============================================================
class CreationNode(models.Model):
    """创作节点记录

    对应 7 节点流水线的每一步：
    1 - 输入解析
    2 - 剧本结构设计
    3 - 人物设定
    4 - 分集大纲
    5 - 剧本正文生成
    6 - 审核与修订
    7 - 导出成品

    节点详情（中间产物原始数据）由 skill 模块持有，此处仅记录元信息。
    """

    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_PENDING, "未开始"),
        (STATUS_RUNNING, "进行中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
    ]

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
        verbose_name="节点ID",
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="nodes",
        verbose_name="所属项目",
    )
    node_index = models.IntegerField("节点编号", help_text="1-7")
    fusion_node_id = models.CharField(
        "融合节点ID",
        max_length=64,
        blank=True,
        default="",
        help_text="如 node-6-review / node-8-score，来自 project-config",
    )
    node_name = models.CharField("节点名称", max_length=100)
    node_description = models.CharField(
        "节点描述", max_length=300, blank=True, default=""
    )

    # 节点角色（来自 StoryForge 生成/评估隔离模型）
    # review/score 节点的上下文必须与 create 节点严格隔离，避免自评偏差
    ROLE_CREATE = "create"      # 内容生成：世界观/人设/大纲/剧本
    ROLE_REVIEW = "review"      # 质量审核：只读已落盘产物，不读实时中间产物
    ROLE_FIX = "fix"            # 内容修复：消费 review 报告，不读 create 中间产物
    ROLE_SCORE = "score"        # 剧本评分：独立上下文，最终量化
    ROLE_DELIVER = "deliver"    # 交付导出：打包/导出
    ROLE_UNSET = ""             # 未设定（旧节点兼容）

    NODE_ROLE_CHOICES = [
        (ROLE_CREATE, "内容生成"),
        (ROLE_REVIEW, "质量审核"),
        (ROLE_FIX, "内容修复"),
        (ROLE_SCORE, "剧本评分"),
        (ROLE_DELIVER, "交付导出"),
        (ROLE_UNSET, "未设定"),
    ]

    node_role = models.CharField(
        "节点角色",
        max_length=16,
        choices=NODE_ROLE_CHOICES,
        default=ROLE_UNSET,
        blank=True,
        db_index=True,
        help_text=(
            "review/score 节点必须通过 get_reviewable_artifact() 接口读取产物，"
            "禁止直接读取同项目 create 节点的实时中间产物，避免自评偏差。"
        ),
    )

    status = models.CharField(
        "状态", max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    # 用于前端展示的进度摘要（由服务层写入，不解析原始结构）
    summary_text = models.TextField(
        "节点摘要文本", blank=True, default="",
        help_text="节点完成后的简短可读描述，用于生成 progress HTML",
    )

    started_at = models.DateTimeField("开始时间", null=True, blank=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    duration_seconds = models.IntegerField("耗时(秒)", default=0)

    error_message = models.TextField("错误信息", blank=True, default="")

    # ── 收敛停机字段（来自 StoryForge 四态控制模型） ──────────────────────
    # 用于 review/fix 类节点的自动修复回路控制
    CONVERGENCE_PENDING = "pending"     # 初始：数据不足，尚未判定
    CONVERGENCE_CONVERGE = "converge"   # 收敛：当轮分 > 上轮分，可继续
    CONVERGENCE_STAGNATE = "stagnate"   # 停滞：差值 ≤ delta，停机
    CONVERGENCE_DIVERGE = "diverge"     # 发散：当轮分 < 上轮分，停机
    CONVERGENCE_OSCILLATE = "oscillate" # 振荡：窗口内有涨有跌，停机
    CONVERGENCE_BLOCKED = "blocked"     # 已停机（含硬上限触发）

    CONVERGENCE_CHOICES = [
        (CONVERGENCE_PENDING, "初始"),
        (CONVERGENCE_CONVERGE, "收敛中"),
        (CONVERGENCE_STAGNATE, "停滞"),
        (CONVERGENCE_DIVERGE, "发散"),
        (CONVERGENCE_OSCILLATE, "振荡"),
        (CONVERGENCE_BLOCKED, "已停机"),
    ]

    fix_round = models.IntegerField(
        "修复轮次", default=0,
        help_text="当前已执行的修复轮数，每次 fix-episode 完成后 +1",
    )
    max_fix_rounds = models.IntegerField(
        "最大修复轮次", default=5,
        help_text="硬上限，由 skill-thresholds.json#maxFixRounds 按节点类型覆盖",
    )
    score_history = models.JSONField(
        "分数历史", default=list, blank=True,
        help_text="每轮修复后的 total_score 列表 [s1, s2, ...]，由 ConvergenceService 追加",
    )
    convergence_state = models.CharField(
        "收敛状态", max_length=16,
        choices=CONVERGENCE_CHOICES,
        default=CONVERGENCE_PENDING,
    )
    fix_blocked_reason = models.CharField(
        "停机原因", max_length=500, blank=True, default="",
        help_text="convergence_state=blocked 时填充，供 Agent/前端展示",
    )
    last_failed_dimensions = models.JSONField(
        "上轮失败维度", default=list, blank=True,
        help_text=(
            "上一轮 review 中未通过的维度 key 列表（G-Eval 模式）。"
            "下轮 review 时只复查这些维度，防止维度漂移。"
            "示例：['pacing', 'plot_structure', 'compliance']"
        ),
    )
    # ────────────────────────────────────────────────────────────────────

    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "创作节点"
        verbose_name_plural = verbose_name
        ordering = ["project_id", "node_index"]
        indexes = [
            models.Index(fields=["project_id", "node_index"]),
            models.Index(fields=["status"]),
            models.Index(fields=["convergence_state"]),
        ]
        unique_together = [["project", "node_index"]]

    def __str__(self) -> str:
        return f"Node {self.node_index} - {self.node_name} ({self.get_status_display()})"


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
# AgentExecutionRun / SubSkillExecutionLog - 技能链执行追踪
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
        ]

    def __str__(self) -> str:
        return f"{self.agent_id} node={self.node_index} {self.status}"


class SubSkillExecutionLog(models.Model):
    """Agent 内单个子技能步骤记录。"""

    STATUS_EXECUTED = "executed"
    STATUS_FAILED = "failed"
    STATUS_SKIPPED = "skipped"

    STATUS_CHOICES = [
        (STATUS_EXECUTED, "已执行"),
        (STATUS_FAILED, "失败"),
        (STATUS_SKIPPED, "跳过"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        AgentExecutionRun,
        on_delete=models.CASCADE,
        related_name="sub_skill_logs",
        verbose_name="执行记录",
    )
    skill_id = models.CharField("子技能 ID", max_length=128, db_index=True)
    skill_type = models.CharField("类型", max_length=32, blank=True, default="")
    cli = models.CharField("CLI", max_length=64, blank=True, default="")
    script = models.CharField("脚本", max_length=128, blank=True, default="")
    status = models.CharField("状态", max_length=16, choices=STATUS_CHOICES, db_index=True)
    attempt = models.PositiveSmallIntegerField("尝试次数", default=1)
    order_index = models.PositiveSmallIntegerField("顺序", default=0)
    input_summary = models.JSONField("输入摘要", default=dict, blank=True)
    output_summary = models.JSONField("输出摘要", default=dict, blank=True)
    error_message = models.TextField("错误信息", blank=True, default="")
    duration_ms = models.PositiveIntegerField("耗时(ms)", null=True, blank=True)
    started_at = models.DateTimeField("开始时间", default=timezone.now)
    finished_at = models.DateTimeField("结束时间", null=True, blank=True)

    class Meta:
        db_table = "creation_sub_skill_execution_log"
        verbose_name = "子技能执行记录"
        verbose_name_plural = verbose_name
        ordering = ["order_index", "started_at"]
        indexes = [
            models.Index(fields=["run", "order_index"]),
            models.Index(fields=["skill_id", "-started_at"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["run", "skill_id"], name="uniq_sub_skill_per_run"),
        ]

    def __str__(self) -> str:
        return f"{self.skill_id} {self.status}"


# ============================================================
# ScriptQualityDefect：剧本质量缺陷记录
# ============================================================
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


# ============================================================
# CreationTask - 统一任务记录（新增，对应统一调度引擎）
# ============================================================
class CreationTask(models.Model):
    """统一创作任务记录

    统一收口 auto/step/workspace 三种模式的任务执行记录，
    与 Project.fusion_status 互为 SSOT：
    - CreationTask 记录一次「技能调用/工作流执行」的完整生命周期
    - Project.fusion_status 记录项目整体创作阶段

    状态机：
      pending → running → completed
                       ↘ failed → retrying → running
                       ↘ cancelled
      running → paused (step 模式等待用户确认 / human_node)
      paused  → running (用户确认)
    """

    STATE_PENDING   = "pending"
    STATE_RUNNING   = "running"
    STATE_PAUSED    = "paused"
    STATE_COMPLETED = "completed"
    STATE_FAILED    = "failed"
    STATE_RETRYING  = "retrying"
    STATE_CANCELLED = "cancelled"

    STATE_CHOICES = [
        (STATE_PENDING,   "待执行"),
        (STATE_RUNNING,   "执行中"),
        (STATE_PAUSED,    "已暂停"),
        (STATE_COMPLETED, "已完成"),
        (STATE_FAILED,    "已失败"),
        (STATE_RETRYING,  "重试中"),
        (STATE_CANCELLED, "已取消"),
    ]

    TRIGGER_AUTO      = "auto"
    TRIGGER_STEP      = "step"
    TRIGGER_WORKSPACE = "workspace"
    TRIGGER_RETRY     = "retry"

    TRIGGER_CHOICES = [
        (TRIGGER_AUTO,      "一键生成"),
        (TRIGGER_STEP,      "分步掌控"),
        (TRIGGER_WORKSPACE, "技能工作台"),
        (TRIGGER_RETRY,     "人工重试"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE,
        related_name="tasks", verbose_name="所属项目",
    )
    workflow = models.ForeignKey(
        "workflow.FusionPipelinePack",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="tasks", verbose_name="工作流版本",
    )
    trigger_mode = models.CharField(
        "触发模式", max_length=16, choices=TRIGGER_CHOICES, default=TRIGGER_WORKSPACE,
    )
    state = models.CharField(
        "执行状态", max_length=16, choices=STATE_CHOICES, default=STATE_PENDING, db_index=True,
    )
    current_node_index = models.IntegerField("当前节点", default=0)
    progress_percent   = models.PositiveSmallIntegerField("进度（%）", default=0)
    celery_task_id     = models.CharField("Celery Task ID", max_length=255, blank=True, default="")
    error_code         = models.CharField("错误码", max_length=64, blank=True, default="")
    error_message      = models.TextField("错误信息", blank=True, default="")
    retry_count        = models.PositiveSmallIntegerField("重试次数", default=0)
    extra              = models.JSONField(
        "扩展参数", default=dict, blank=True,
        help_text="存储 node_index、options 等调用参数快照，便于重试恢复",
    )
    started_at   = models.DateTimeField("开始时间", null=True, blank=True)
    completed_at = models.DateTimeField("完成时间", null=True, blank=True)
    created_at   = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at   = models.DateTimeField("更新时间", auto_now=True)

    class Meta:
        db_table = "creation_task"
        verbose_name = "创作任务"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "state"], name="task_project_state_idx"),
            models.Index(fields=["state", "-created_at"], name="task_state_time_idx"),
        ]

    def __str__(self) -> str:
        return f"Task[{self.trigger_mode}] {self.id.hex[:8]} - {self.get_state_display()}"

    def transition(self, new_state: str, *, error_code: str = "", error_message: str = "") -> None:
        """状态机流转，统一入口"""
        fields = ["state", "updated_at"]
        self.state = new_state
        if new_state == self.STATE_RUNNING and not self.started_at:
            self.started_at = timezone.now()
            fields.append("started_at")
        if new_state in (self.STATE_COMPLETED, self.STATE_FAILED, self.STATE_CANCELLED):
            self.completed_at = timezone.now()
            fields.append("completed_at")
        if error_code:
            self.error_code = error_code
            self.error_message = error_message
            fields += ["error_code", "error_message"]
        self.save(update_fields=fields)
