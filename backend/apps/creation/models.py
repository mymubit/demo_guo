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
    STATUS_COMPLETED = "completed"  # 完成
    STATUS_FAILED = "failed"        # 失败

    STATUS_CHOICES = [
        (STATUS_PENDING, "排队中"),
        (STATUS_RUNNING, "创作中"),
        (STATUS_COMPLETED, "已完成"),
        (STATUS_FAILED, "失败"),
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
        "参考作品", max_length=200, blank=True, default=""
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
    current_node_index = models.IntegerField(
        "当前节点索引", default=0, help_text="0 表示未开始，1-7 表示正在/已完成该节点"
    )
    total_nodes = models.IntegerField("总节点数", default=7)
    progress_percent = models.IntegerField("进度百分比", default=0)
    error_message = models.TextField(
        "错误信息", blank=True, default="", help_text="status=failed 时填充"
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

    class Meta:
        verbose_name = "创作项目"
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["status"]),
        ]

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
    node_name = models.CharField("节点名称", max_length=100)
    node_description = models.CharField(
        "节点描述", max_length=300, blank=True, default=""
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

    created_at = models.DateTimeField("创建时间", default=timezone.now)

    class Meta:
        verbose_name = "创作节点"
        verbose_name_plural = verbose_name
        ordering = ["project_id", "node_index"]
        indexes = [
            models.Index(fields=["project_id", "node_index"]),
            models.Index(fields=["status"]),
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
