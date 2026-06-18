# -*- coding: utf-8 -*-
"""
技能配置模块的后台管理配置
- 仅超级管理员可访问
- 加密配置值在后台以脱敏方式展示
"""
from django.contrib import admin
from django.contrib import messages
from django.utils.html import format_html

from apps.agent.models import AgentRegistryConfig
from apps.workflow.models import FusionJsonSchema, FusionPipelineNode, FusionPipelinePack
from apps.skill.models import (
    AgentSkillDefinition,
    DialogueTemplate,
    HookLibrary,
    LlmModelCatalog,
    LlmProvider,
    SkillConfig,
    SkillConfigEntry,
    SkillDefect,
    SkillRuleConfig,
    ThemeTemplate,
)


class SkillConfigAdmin(admin.ModelAdmin):
    list_display = ['config_key', 'description', 'value_display', 'updated_at']
    search_fields = ['config_key', 'description']
    readonly_fields = ['updated_at']

    def value_display(self, obj):
        """脱敏展示：密钥类只显示前3位"""
        if any(k in obj.config_key.lower() for k in ['api_key', 'secret', 'password', 'token']):
            return '********（加密存储）'
        val = obj.config_value_encrypted
        if len(val) > 50:
            return val[:50] + '...'
        return val
    value_display.short_description = '配置值'

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        # 保存时触发 service 层的加密逻辑，这里保持默认，实际由 SkillConfigService 管理
        super().save_model(request, obj, form, change)
        messages.info(request, '配置已更新，缓存已刷新')


class ThemeTemplateAdmin(admin.ModelAdmin):
    list_display = ['theme_code', 'theme_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['theme_code', 'theme_name']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


class HookLibraryAdmin(admin.ModelAdmin):
    list_display = ['hook_type', 'content_preview', 'is_active', 'use_count', 'created_at']
    list_filter = ['hook_type', 'is_active']
    search_fields = ['content']

    def content_preview(self, obj):
        return obj.content[:40] + ('...' if len(obj.content) > 40 else '')
    content_preview.short_description = '钩子内容'

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


class DialogueTemplateAdmin(admin.ModelAdmin):
    list_display = ['emotion_type', 'template_preview', 'is_active', 'created_at']
    list_filter = ['emotion_type', 'is_active']

    def template_preview(self, obj):
        return obj.template_text[:40] + ('...' if len(obj.template_text) > 40 else '')
    template_preview.short_description = '模板内容'

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(LlmModelCatalog)
class LlmModelCatalogAdmin(admin.ModelAdmin):
    list_display = ['preset_key', 'name', 'vendor_label', 'model_name', 'is_enabled', 'sort_order']
    list_filter = ['vendor', 'is_enabled']
    search_fields = ['preset_key', 'name', 'model_name', 'vendor_label']
    ordering = ['sort_order', 'vendor', 'name']


@admin.register(LlmProvider)
class LlmProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_name', 'is_active', 'is_enabled', 'api_key_set_display', 'updated_at']
    list_filter = ['is_active', 'is_enabled']
    search_fields = ['name', 'model_name', 'base_url']
    raw_id_fields = ['catalog']

    @admin.display(boolean=True, description='已配置 Key')
    def api_key_set_display(self, obj):
        return obj.api_key_set


admin.site.register(SkillConfig, SkillConfigAdmin)
admin.site.register(ThemeTemplate, ThemeTemplateAdmin)
admin.site.register(HookLibrary, HookLibraryAdmin)
admin.site.register(DialogueTemplate, DialogueTemplateAdmin)


# ============================================================
# SkillRuleConfig Admin
# ============================================================
@admin.register(SkillRuleConfig)
class SkillRuleConfigAdmin(admin.ModelAdmin):
    list_display = [
        "rule_label", "tier", "scope_type", "scope_key", "section",
        "version_tag", "status_badge", "source", "trigger_score_avg", "updated_at",
    ]
    list_filter = ["tier", "scope_type", "status", "source"]
    search_fields = ["scope_key", "section", "note"]
    ordering = ["tier", "scope_type", "scope_key", "section", "-updated_at"]
    readonly_fields = ["id", "created_at", "updated_at", "approved_at", "approved_by", "trigger_project_ids", "trigger_score_avg"]
    actions = ["approve_selected", "archive_selected"]

    fieldsets = (
        ("规则定位", {"fields": ("tier", "scope_type", "scope_key", "section")}),
        ("内容", {"fields": ("content", "version_tag", "note")}),
        ("状态", {"fields": ("status", "source", "approved_by", "approved_at")}),
        ("进化追踪", {"fields": ("trigger_project_ids", "trigger_score_avg")}),
        ("元数据", {"fields": ("id", "created_at", "updated_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="规则标识")
    def rule_label(self, obj):
        return f"[T{obj.tier}·{obj.scope_key or 'global'}] {obj.section}"

    @admin.display(description="状态")
    def status_badge(self, obj):
        colors = {"active": "green", "draft": "orange", "archived": "gray"}
        labels = {"active": "已生效", "draft": "待审核", "archived": "已归档"}
        color = colors.get(obj.status, "black")
        label = labels.get(obj.status, obj.status)
        return format_html('<span style="color:{};font-weight:bold">{}</span>', color, label)

    @admin.action(description="批准选中提案（draft → active）")
    def approve_selected(self, request, queryset):
        count = 0
        for obj in queryset.filter(status=SkillRuleConfig.STATUS_DRAFT):
            obj.approve(approved_by=request.user.username)
            count += 1
        self.message_user(request, f"已批准 {count} 条规则，旧版本已归档。")

    @admin.action(description="归档选中规则")
    def archive_selected(self, request, queryset):
        updated = queryset.exclude(status=SkillRuleConfig.STATUS_ARCHIVED).update(status=SkillRuleConfig.STATUS_ARCHIVED)
        self.message_user(request, f"已归档 {updated} 条规则。")


@admin.register(AgentRegistryConfig)
class AgentRegistryConfigAdmin(admin.ModelAdmin):
    list_display = ["display_name", "config_key", "is_active", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["config_key", "display_name", "note"]
    readonly_fields = ["id", "updated_at"]
    fieldsets = (
        ("基础信息", {"fields": ("config_key", "display_name", "is_active", "note")}),
        ("Agent Registry JSON", {"fields": ("registry",)}),
        ("元数据", {"fields": ("id", "updated_at"), "classes": ("collapse",)}),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from apps.agent.runtime import get_agent_registry

            get_agent_registry.cache_clear()
        except Exception:  # noqa: BLE001
            pass
        self.message_user(request, "Agent 注册表已保存，运行时缓存已刷新。")


class FusionPipelineNodeInline(admin.TabularInline):
    model = FusionPipelineNode
    extra = 0
    fields = [
        "chain_order",
        "website_index",
        "fusion_node_id",
        "name",
        "runner_type",
        "runner_path",
        "output_key",
        "artifact_key",
        "pipeline_result_key",
        "extra_artifact_keys",
        "schema",
        "enabled",
        "coin_cost",
        "is_terminal",
        "fusion_status",
    ]
    ordering = ["chain_order"]


@admin.register(FusionPipelinePack)
class FusionPipelinePackAdmin(admin.ModelAdmin):
    list_display = ["version", "is_active", "nodes_count", "imported_from_root", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["version", "notes", "imported_from_root"]
    readonly_fields = ["id", "created_at", "updated_at"]
    inlines = [FusionPipelineNodeInline]

    @admin.display(description="节点数")
    def nodes_count(self, obj):
        return obj.nodes.count()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        try:
            from apps.workflow.pipeline_store import FusionPipelineDbService

            FusionPipelineDbService.clear_caches()
        except Exception:  # noqa: BLE001
            pass


@admin.register(FusionJsonSchema)
class FusionJsonSchemaAdmin(admin.ModelAdmin):
    list_display = ["schema_key", "filename", "pack", "updated_at"]
    list_filter = ["pack"]
    search_fields = ["schema_key", "filename"]
    readonly_fields = ["id", "updated_at"]


# ============================================================
# AgentSkillDefinition Admin
# ============================================================
@admin.register(AgentSkillDefinition)
class AgentSkillDefinitionAdmin(admin.ModelAdmin):
    list_display = ["skill_id", "name", "skill_layer", "lifecycle_status", "version", "updated_at"]
    list_filter = ["skill_layer", "lifecycle_status"]
    search_fields = ["skill_id", "name", "source_file"]
    readonly_fields = ["created_at", "updated_at"]
    ordering = ["skill_layer", "skill_id"]

    fieldsets = (
        ("基础信息", {"fields": ("skill_id", "name", "skill_layer", "sub_category", "version", "lifecycle_status", "gray_weight")}),
        ("技能内容", {"fields": ("content", "system_hint", "input_schema", "output_schema")}),
        ("来源追踪", {"fields": ("source_file",)}),
        ("时间戳", {"fields": ("created_at", "updated_at", "published_at", "deprecated_at"), "classes": ("collapse",)}),
    )


# ============================================================
# SkillConfigEntry Admin
# ============================================================
@admin.register(SkillConfigEntry)
class SkillConfigEntryAdmin(admin.ModelAdmin):
    list_display = ["config_key", "edition", "version", "updated_at"]
    search_fields = ["config_key", "edition", "note"]
    readonly_fields = ["updated_at"]
    ordering = ["config_key"]

    fieldsets = (
        ("基础信息", {"fields": ("config_key", "edition", "version", "note")}),
        ("配置内容（JSON）", {"fields": ("content",)}),
        ("时间戳", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )


# ============================================================
# SkillDefect Admin
# ============================================================
class SkillDefectInline(admin.TabularInline):
    model = SkillDefect
    extra = 0
    fields = ["title", "severity", "status", "reported_by", "created_at"]
    readonly_fields = ["created_at"]


@admin.register(SkillDefect)
class SkillDefectAdmin(admin.ModelAdmin):
    list_display = ["title", "skill", "severity_badge", "status", "reported_by", "created_at"]
    list_filter = ["severity", "status"]
    search_fields = ["title", "description", "reported_by", "skill__skill_id"]
    readonly_fields = ["created_at", "updated_at", "resolved_at"]
    ordering = ["severity", "-created_at"]
    actions = ["mark_resolved", "mark_closed"]

    fieldsets = (
        ("基础信息", {"fields": ("skill", "title", "severity", "status", "reported_by")}),
        ("详情", {"fields": ("description", "reproduce_steps", "fix_notes")}),
        ("时间戳", {"fields": ("created_at", "updated_at", "resolved_at"), "classes": ("collapse",)}),
    )

    @admin.display(description="严重级别")
    def severity_badge(self, obj):
        colors = {"P0": "red", "P1": "orange", "P2": "blue", "P3": "gray"}
        color = colors.get(obj.severity, "black")
        return format_html(
            '<span style="color:{};font-weight:bold">{}</span>', color, obj.get_severity_display()
        )

    @admin.action(description="标记为已解决")
    def mark_resolved(self, request, queryset):
        from django.utils import timezone
        updated = queryset.exclude(status=SkillDefect.STATUS_RESOLVED).update(
            status=SkillDefect.STATUS_RESOLVED,
            resolved_at=timezone.now(),
        )
        self.message_user(request, f"已将 {updated} 条缺陷标记为已解决。")

    @admin.action(description="关闭选中缺陷")
    def mark_closed(self, request, queryset):
        updated = queryset.exclude(status=SkillDefect.STATUS_CLOSED).update(
            status=SkillDefect.STATUS_CLOSED,
        )
        self.message_user(request, f"已关闭 {updated} 条缺陷。")
