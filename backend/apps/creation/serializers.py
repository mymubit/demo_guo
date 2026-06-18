"""
创作模块序列化器

核心安全原则：
- 绝不暴露原始剧本数据结构
- 所有剧本内容以预渲染 HTML 片段形式返回
- 进度与结果仅提供状态 + HTML，不解析内部结构
"""

import re

from rest_framework import serializers

from .models import Project, ScriptWork, ShareLink


# ============================================================
# 创作提交请求
# ============================================================
class CreationSubmitSerializer(serializers.Serializer):
    """提交创作请求

    仅接受用户输入的创作参数，内部校验会员状态与创作次数。
    """

    theme = serializers.CharField(
        max_length=64,
        error_messages={
            "blank": "请选择题材",
            "max_length": "题材代码过长",
        },
        help_text="题材代码，如 family-revenge / overbearing-ceo",
    )
    core_idea = serializers.CharField(
        max_length=1000,
        error_messages={
            "blank": "请填写核心创意",
            "max_length": "核心创意最多 1000 字",
        },
        help_text="一句话核心创意描述",
    )
    episode_count = serializers.IntegerField(
        min_value=10,
        max_value=500,
        default=30,
        error_messages={
            "min_value": "集数至少 10 集",
            "max_value": "集数最多 500 集",
        },
        help_text="剧本集数（10-500）",
    )
    format_variant = serializers.ChoiceField(
        choices=[("A", "变体 A"), ("B", "变体 B"), ("C", "变体 C"), ("D", "变体 D")],
        default="B",
        help_text="输出格式变体，默认 B",
    )
    audience = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        default="",
        help_text="目标受众描述（可选）",
    )
    reference_work = serializers.CharField(
        max_length=2000,
        required=False,
        allow_blank=True,
        default="",
        help_text="参考作品（可选）",
    )
    outline_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="已有分集大纲（from-outline）",
    )
    novel_text = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="小说原文（novel-adaptation）",
    )
    ip_sequel_mode = serializers.ChoiceField(
        choices=[("sequel", "续作"), ("prequel", "前传"), ("spin-off", "衍生")],
        required=False,
        allow_blank=True,
        default="sequel",
    )
    ip_keep_rules = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="IP 须保持的规则说明",
    )
    target_platform = serializers.CharField(
        max_length=32,
        default="douyin",
        required=False,
        help_text="平台代码，合法值见 GET /api/creation/fusion/catalog/",
    )
    episode_duration_minutes = serializers.FloatField(
        min_value=0.5,
        max_value=30,
        default=2.0,
        required=False,
    )
    creation_entry = serializers.CharField(
        max_length=32,
        default="from-scratch",
        required=False,
    )
    budget_level = serializers.ChoiceField(
        choices=[("low", "低预算"), ("medium", "中预算"), ("high", "高预算")],
        default="medium",
        required=False,
    )
    global_market = serializers.ChoiceField(
        choices=[("domestic", "国内"), ("global", "出海")],
        default="domestic",
        required=False,
    )
    pipeline_mode = serializers.ChoiceField(
        choices=[
            ("workspace", "技能工作台"),
            ("auto", "一键生成"),
            ("step", "分步掌控"),
        ],
        default="workspace",
        required=False,
        help_text="workspace=按技能模块；auto=后台连续执行；step=每节点暂停待确认",
    )
    pipeline_pack_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="创作流水线模板 ID，见 catalog.publishedPipelines",
    )

    def validate_pipeline_pack_id(self, value):
        if value is None:
            return value
        from apps.workflow.pipeline_store import FusionPipelineDbService

        pack = FusionPipelineDbService.get_pack_by_id(str(value))
        if pack is None:
            raise serializers.ValidationError("流水线模板不存在")
        if not pack.is_published_to_portal:
            raise serializers.ValidationError("该流水线尚未对创作入口开放")
        if not pack.nodes.exists():
            raise serializers.ValidationError("流水线模板无有效步骤")
        return value

    def validate_theme(self, value):
        """题材代码校验：允许 小写字母、数字、连字符"""
        if not re.match(r"^[a-z][a-z0-9-]{1,62}[a-z0-9]$", value):
            raise serializers.ValidationError("题材代码格式不正确")
        return value

    def validate_core_idea(self, value):
        value = value.strip()
        if len(value) < 5:
            raise serializers.ValidationError("核心创意描述过短")
        return value

    def validate_creation_entry(self, value):
        value = (value or "from-scratch").strip()
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        allowed = set(CreationFormOverrideService.allowed_creation_entries())
        if value not in allowed:
            raise serializers.ValidationError("创作入口不在后台配置范围内")
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        entry = attrs.get("creation_entry") or "from-scratch"
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        validation = CreationFormOverrideService.creation_entry_validation(entry)
        required_fields = validation.get("requiredFields") if isinstance(validation, dict) else {}
        errors = {}
        field_labels = {
            "reference_work": "参考作品说明",
            "outline_text": "分集大纲",
            "novel_text": "小说原文",
            "ip_keep_rules": "IP 约束",
        }
        for field, rule in (required_fields or {}).items():
            if not isinstance(rule, dict):
                continue
            min_length = int(rule.get("minLength") or 1)
            label = rule.get("label") or field_labels.get(field) or field
            if len((attrs.get(field) or "").strip()) < min_length:
                errors[field] = f"{label}至少 {min_length} 字"
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


# ============================================================
# 提交创作的返回结果
# ============================================================
class CreationSubmitResultSerializer(serializers.Serializer):
    """提交创作成功返回

    只返回 project_id 与预计时长，不暴露任何原始数据结构。
    """

    project_id = serializers.CharField(help_text="项目ID")
    estimated_minutes = serializers.IntegerField(
        help_text="预计完成时长（分钟）"
    )
    status = serializers.CharField(help_text="项目状态", required=False)
    workspace_url = serializers.CharField(help_text="工作台地址", required=False)


# ============================================================
# 创作进度响应
# ============================================================
class ProjectProgressSerializer(serializers.Serializer):
    """进度查询响应

    安全设计：
    - 仅返回状态和预渲染 HTML 片段
    - 绝不包含任何原始剧本数据结构
    - 完成时额外返回一次性下载 token（15 分钟有效）
    """

    status = serializers.CharField(help_text="pending / running / awaiting / completed / failed")
    status_text = serializers.CharField(help_text="状态中文描述")
    progress_percent = serializers.IntegerField(help_text="进度百分比 0-100")
    rendered_progress_html = serializers.CharField(
        help_text="预渲染的进度卡片 HTML 片段"
    )
    rendered_result_html = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="完成时返回：预渲染的剧本结果 HTML（含水印）",
    )
    download_token = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="一次性下载 token，15 分钟有效",
    )
    error_message = serializers.CharField(
        required=False,
        allow_blank=True,
        default="",
        help_text="失败时的错误信息（用户可读）",
    )
    fusion_status = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    fusion_status_text = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    overall_score = serializers.FloatField(required=False, allow_null=True)
    grade = serializers.CharField(required=False, allow_blank=True, default="")
    ready_at = serializers.DateTimeField(required=False, allow_null=True)
    skill_version = serializers.CharField(required=False, allow_blank=True, default="")
    score_summary = serializers.DictField(required=False, allow_null=True)
    pipeline_mode = serializers.CharField(required=False, default="auto")
    latest_execution_run = serializers.DictField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(help_text="任务提交时间")
    updated_at = serializers.DateTimeField(help_text="最近更新时间")


# ============================================================
# 作品列表
# ============================================================
class ProjectListSerializer(serializers.Serializer):
    """我的作品列表项序列化器

    仅展示元信息（标题、状态、创建时间、集数等），
    绝不包含任何剧本正文内容。
    """

    project_id = serializers.CharField(source="id", help_text="项目ID")
    title = serializers.CharField(help_text="剧本标题")
    theme = serializers.CharField(help_text="题材")
    episode_count = serializers.IntegerField(help_text="集数")
    format_variant = serializers.CharField(help_text="输出格式变体")
    status = serializers.CharField(help_text="项目状态")
    status_text = serializers.SerializerMethodField(help_text="状态中文描述")
    progress_percent = serializers.IntegerField(help_text="进度百分比")
    fusion_status = serializers.CharField(
        required=False, allow_blank=True, default="",
    )
    overall_score = serializers.FloatField(required=False, allow_null=True)
    grade = serializers.CharField(required=False, allow_blank=True, default="")
    ready_at = serializers.DateTimeField(required=False, allow_null=True)
    created_at = serializers.DateTimeField(help_text="创建时间")
    updated_at = serializers.DateTimeField(help_text="更新时间")

    core_idea = serializers.SerializerMethodField(help_text="核心创意摘要")
    pipeline_mode = serializers.CharField(help_text="创作模式")
    creation_entry = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="创作入口"
    )

    def get_status_text(self, obj) -> str:
        return obj.get_status_display()

    def get_core_idea(self, obj) -> str:
        text = (obj.core_idea or "").strip()
        if len(text) <= 320:
            return text
        return text[:320] + "…"


# ============================================================
# 生成分享链接
# ============================================================
class ShareCreateSerializer(serializers.Serializer):
    """生成分享链接请求"""

    project_id = serializers.CharField(
        required=False,
        help_text="项目ID（可通过 URL 路径传入）",
    )
    view_limit = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=1000,
        default=100,
        help_text="最大查看次数，默认 100",
    )
    valid_days = serializers.IntegerField(
        required=False,
        min_value=1,
        max_value=30,
        default=7,
        help_text="有效天数（1-30），默认 7",
    )
    allow_download = serializers.BooleanField(
        required=False,
        default=False,
        help_text="是否允许在分享页下载",
    )
    custom_title = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=200,
        default="",
        help_text="自定义分享标题（可选）",
    )


class ShareCreateResultSerializer(serializers.Serializer):
    """生成分享链接返回"""

    share_id = serializers.CharField(help_text="分享记录ID")
    share_token = serializers.CharField(help_text="分享 token（用于构造 URL）")
    share_url = serializers.CharField(
        help_text="完整分享链接（前端域名 + /share/{token}）"
    )
    expires_at = serializers.DateTimeField(help_text="过期时间")
    view_limit = serializers.IntegerField(help_text="最大查看次数")
    allow_download = serializers.BooleanField(help_text="是否允许下载")
    custom_title = serializers.CharField(
        required=False, allow_blank=True, default="",
        help_text="自定义分享标题",
    )


# ============================================================
# 下载参数（URL 路径参数用，非 body 校验）
# ============================================================
class DownloadFormatSerializer(serializers.Serializer):
    """下载格式校验"""

    file_format = serializers.ChoiceField(
        choices=["md", "html", "zip", "pdf"],
        default="md",
        help_text="下载格式",
    )


# ============================================================
# 分享页面元信息（公开访问用，绝不暴露创作数据结构）
# ============================================================
class ShareViewSerializer(serializers.Serializer):
    """分享页面元信息"""

    title = serializers.CharField(help_text="分享标题")
    author_nickname = serializers.CharField(help_text="创建者昵称")
    created_at = serializers.DateTimeField(help_text="分享创建时间")
    expires_at = serializers.DateTimeField(help_text="过期时间")
    remain_views = serializers.IntegerField(help_text="剩余可查看次数")
    allow_download = serializers.BooleanField(help_text="是否允许下载")
    # 预渲染的分享页 HTML 片段，含水印，前端直接插入
    rendered_share_html = serializers.CharField(
        help_text="预渲染的分享页 HTML 内容（含水印）"
    )
