"""
创作模块 Django Admin 配置

注意：
- 后台可见 Project / CreationNode / ScriptWork / ShareLink 的完整字段
- 不提供对原始剧本数据的直接编辑（也没有存储原始剧本）
- ScriptWork.storage_path 为文件路径，不在 admin 暴露原始数据
"""

from django.contrib import admin

from django.utils.html import format_html

from .models import (
    AgentExecutionRun,
    CreationNode,
    DownloadToken,
    Project,
    ProjectFusionArtifact,
    ScriptQualityDefect,
    ScriptWork,
    ShareLink,
    SubSkillExecutionLog,
)


# ============================================================
# Project Admin
# ============================================================
class CreationNodeInline(admin.TabularInline):
    """节点记录内联显示

    便于在 Project 详情页查看各节点的执行情况。
    """

    model = CreationNode
    fields = ("node_index", "node_name", "status", "duration_seconds")
    readonly_fields = fields
    extra = 0
    can_delete = False


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        "id_hex",
        "user_id",
        "theme",
        "episode_count",
        "format_variant",
        "status",
        "fusion_status",
        "overall_score",
        "grade",
        "progress_percent",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "fusion_status", "format_variant", "created_at")
    search_fields = ("id", "user__id", "theme", "title")
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
        "completed_at",
        "rendered_progress_html",
        "rendered_result_html",
    )
    exclude = ("core_idea",)  # 创意描述不在 admin 直接展示，避免误操作
    inlines = [CreationNodeInline]
    ordering = ("-created_at",)

    def id_hex(self, obj) -> str:
        return str(obj.id).split("-")[0] if obj.id else ""

    id_hex.short_description = "项目ID"


# ============================================================
# ScriptWork Admin
# ============================================================
@admin.register(ScriptWork)
class ScriptWorkAdmin(admin.ModelAdmin):
    list_display = (
        "id_hex",
        "project_id_hex",
        "file_format",
        "file_name",
        "size_bytes",
        "watermark_token",
        "created_at",
    )
    list_filter = ("file_format", "created_at")
    search_fields = ("project__id", "watermark_token", "file_name")
    readonly_fields = ("id", "storage_path", "watermark_token", "created_at")
    ordering = ("-created_at",)

    def id_hex(self, obj) -> str:
        return str(obj.id).split("-")[0] if obj.id else ""

    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    id_hex.short_description = "文件ID"
    project_id_hex.short_description = "项目ID"


# ============================================================
# ShareLink Admin
# ============================================================
@admin.register(ShareLink)
class ShareLinkAdmin(admin.ModelAdmin):
    list_display = (
        "token_short",
        "project_id_hex",
        "user_id",
        "view_count",
        "view_limit",
        "allow_download",
        "is_active",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_active", "allow_download", "created_at")
    search_fields = ("token", "project__id")
    readonly_fields = ("id", "token", "created_at", "last_viewed_at")
    ordering = ("-created_at",)

    def token_short(self, obj) -> str:
        return obj.token[:12] if obj.token else ""

    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    token_short.short_description = "分享Token"
    project_id_hex.short_description = "项目ID"


# ============================================================
# DownloadToken Admin
# ============================================================
@admin.register(DownloadToken)
class DownloadTokenAdmin(admin.ModelAdmin):
    list_display = (
        "token_short",
        "project_id_hex",
        "user_id",
        "is_used",
        "expires_at",
        "created_at",
    )
    list_filter = ("is_used", "created_at")
    search_fields = ("token", "project__id")
    readonly_fields = ("id", "token", "used_at", "created_at")
    ordering = ("-created_at",)

    def token_short(self, obj) -> str:
        return obj.token[:12] if obj.token else ""

    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    token_short.short_description = "下载Token"
    project_id_hex.short_description = "项目ID"


class SubSkillExecutionLogInline(admin.TabularInline):
    model = SubSkillExecutionLog
    fields = (
        "skill_id",
        "status",
        "skill_type",
        "duration_ms",
        "error_message",
        "order_index",
    )
    readonly_fields = fields
    extra = 0
    can_delete = False
    ordering = ("order_index", "started_at")


@admin.register(AgentExecutionRun)
class AgentExecutionRunAdmin(admin.ModelAdmin):
    list_display = (
        "id_hex",
        "project_id_hex",
        "agent_id",
        "node_index",
        "status",
        "output_artifact_key",
        "started_at",
        "finished_at",
    )
    list_filter = ("status", "agent_id", "started_at")
    search_fields = ("id", "project__id", "agent_id", "error_message")
    readonly_fields = (
        "id",
        "project",
        "user",
        "input_summary",
        "output_summary",
        "started_at",
        "finished_at",
    )
    inlines = [SubSkillExecutionLogInline]
    ordering = ("-started_at",)

    def id_hex(self, obj) -> str:
        return str(obj.id).split("-")[0] if obj.id else ""

    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    id_hex.short_description = "Run ID"
    project_id_hex.short_description = "项目ID"


@admin.register(SubSkillExecutionLog)
class SubSkillExecutionLogAdmin(admin.ModelAdmin):
    list_display = (
        "skill_id",
        "run_id_hex",
        "status",
        "skill_type",
        "duration_ms",
        "started_at",
    )
    list_filter = ("status", "skill_type")
    search_fields = ("skill_id", "run__id", "error_message")
    readonly_fields = (
        "id",
        "run",
        "input_summary",
        "output_summary",
        "started_at",
        "finished_at",
    )
    ordering = ("-started_at",)

    def run_id_hex(self, obj) -> str:
        return str(obj.run_id).split("-")[0] if obj.run_id else ""

    run_id_hex.short_description = "Run ID"


@admin.register(ProjectFusionArtifact)
class ProjectFusionArtifactAdmin(admin.ModelAdmin):
    list_display = ("project_id_hex", "artifact_key", "version", "updated_at")
    list_filter = ("artifact_key",)
    search_fields = ("project__id", "artifact_key")
    readonly_fields = ("id", "created_at", "updated_at")

    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    project_id_hex.short_description = "项目ID"


# ============================================================
# ScriptQualityDefect Admin
# ============================================================
@admin.register(ScriptQualityDefect)
class ScriptQualityDefectAdmin(admin.ModelAdmin):
    list_display = [
        "project_id_hex", "episode", "dimension", "defect_type",
        "score_display", "source", "status_badge", "created_at",
    ]
    list_filter = ["dimension", "source", "status"]
    search_fields = ["defect_type", "project__id"]
    readonly_fields = ["created_at"]
    ordering = ["-created_at"]
    actions = ["mark_resolved"]

    fieldsets = (
        ("位置", {"fields": ("project", "episode", "dimension", "defect_type")}),
        ("评分与详情", {"fields": ("score", "details")}),
        ("状态", {"fields": ("source", "status")}),
        ("时间戳", {"fields": ("created_at",), "classes": ("collapse",)}),
    )

    @admin.display(description="项目ID")
    def project_id_hex(self, obj) -> str:
        return str(obj.project_id).split("-")[0] if obj.project_id else ""

    @admin.display(description="得分")
    def score_display(self, obj):
        if obj.score is None:
            return "-"
        color = "green" if obj.score >= 75 else ("orange" if obj.score >= 60 else "red")
        return format_html('<span style="color:{}">{:.1f}</span>', color, obj.score)

    @admin.display(description="状态")
    def status_badge(self, obj):
        colors = {"open": "orange", "resolved": "green"}
        color = colors.get(obj.status, "gray")
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>', color, obj.get_status_display()
        )

    @admin.action(description="标记为已处理")
    def mark_resolved(self, request, queryset):
        updated = queryset.exclude(status=ScriptQualityDefect.STATUS_RESOLVED).update(
            status=ScriptQualityDefect.STATUS_RESOLVED,
        )
        self.message_user(request, f"已将 {updated} 条缺陷标记为已处理。")
