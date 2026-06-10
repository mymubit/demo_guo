"""
创作模块 Django Admin 配置

注意：
- 后台可见 Project / CreationNode / ScriptWork / ShareLink 的完整字段
- 不提供对原始剧本数据的直接编辑（也没有存储原始剧本）
- ScriptWork.storage_path 为文件路径，不在 admin 暴露原始数据
"""

from django.contrib import admin

from .models import Project, CreationNode, ScriptWork, ShareLink, DownloadToken


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
        "progress_percent",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "format_variant", "created_at")
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
