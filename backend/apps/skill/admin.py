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
from apps.skill.models import (
    AgentSkillDefinition,
    AgentSkillSection,
    CreationFormOverrideConfig,
    DialogueTemplate,
    HookLibrary,
    LlmModelCatalog,
    LlmProvider,
    SkillConfig,
    SkillConfigEntry,
    SkillDefect,
    SkillRuleConfig,
    SkillRuleItem,
    ThemeTemplate,
)
from apps.skill.models_catalog import (
    ThemeActRatio,
    ThemeCharacterArchetype,
    ThemeEmotionCurve,
    ThemeEmotionalPeakMoment,
    ThemeHookType,
    ThemeReversalDensity,
)
from apps.skill.models_creation_form import (
    CreationBudgetLevel,
    CreationEntry,
    CreationEntryProfile,
    CreationPlatform,
    CreationThemeEntry,
    EpisodeSettingsConfig,
    FormatVariant,
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


class ThemeActRatioInline(admin.TabularInline):
    model = ThemeActRatio
    extra = 0
    fields = ["act_name", "ratio_percent", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeEmotionCurveInline(admin.TabularInline):
    model = ThemeEmotionCurve
    extra = 0
    fields = ["episode_from", "episode_to", "emotion_value", "label", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeHookTypeInline(admin.TabularInline):
    model = ThemeHookType
    extra = 0
    fields = ["hook_type", "description", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeCharacterArchetypeInline(admin.TabularInline):
    model = ThemeCharacterArchetype
    extra = 0
    fields = ["name", "description", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeEmotionalPeakMomentInline(admin.TabularInline):
    model = ThemeEmotionalPeakMoment
    extra = 0
    fields = ["episode_hint", "moment", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeReversalDensityInline(admin.TabularInline):
    model = ThemeReversalDensity
    extra = 0
    fields = ["stage", "density", "sort_order", "is_active"]
    ordering = ["sort_order"]


class ThemeTemplateAdmin(admin.ModelAdmin):
    inlines = [
        ThemeActRatioInline,
        ThemeEmotionCurveInline,
        ThemeHookTypeInline,
        ThemeCharacterArchetypeInline,
        ThemeEmotionalPeakMomentInline,
        ThemeReversalDensityInline,
    ]
    list_display = ['theme_code', 'theme_name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['theme_code', 'theme_name']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if form.instance and formset.model in (
            ThemeActRatio,
            ThemeEmotionCurve,
            ThemeHookType,
            ThemeCharacterArchetype,
            ThemeEmotionalPeakMoment,
            ThemeReversalDensity,
        ):
            from apps.skill.services.theme_atomic_sync import sync_params_from_atomic_tables

            sync_params_from_atomic_tables(form.instance)


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
class SkillRuleItemInline(admin.TabularInline):
    model = SkillRuleItem
    extra = 0
    fields = ["title", "body", "status", "sort_order", "apply_count", "last_applied_at"]
    readonly_fields = ["apply_count", "last_applied_at"]
    show_change_link = True


@admin.register(SkillRuleConfig)
class SkillRuleConfigAdmin(admin.ModelAdmin):
    inlines = [SkillRuleItemInline]
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
        ("内容", {"fields": ("content_source", "content", "version_tag", "note")}),
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


@admin.register(SkillRuleItem)
class SkillRuleItemAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "rule_key",
        "tier",
        "section",
        "status",
        "apply_count",
        "last_applied_at",
        "updated_at",
    ]
    list_filter = ["tier", "status", "item_type", "scope_type"]
    search_fields = ["title", "rule_key", "body", "section"]
    ordering = ["tier", "section", "sort_order", "-apply_count"]


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


# ============================================================
# AgentSkillDefinition Admin
# ============================================================
class AgentSkillSectionInline(admin.TabularInline):
    model = AgentSkillSection
    extra = 0
    fields = ["section_key", "section_content", "sort_order", "is_active"]
    ordering = ["sort_order", "section_key"]


@admin.register(AgentSkillDefinition)
class AgentSkillDefinitionAdmin(admin.ModelAdmin):
    inlines = [AgentSkillSectionInline]
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

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        from apps.skill.skills.skill_section_sync import sync_content_from_sections

        if obj.sections.exists():
            sync_content_from_sections(obj)

    def save_formset(self, request, form, formset, change):
        super().save_formset(request, form, formset, change)
        if formset.model is AgentSkillSection and form.instance:
            from apps.skill.skills.skill_section_sync import sync_content_from_sections

            sync_content_from_sections(form.instance)


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


# ============================================================
# CreationForm 原子 Catalog Admin
# ============================================================
def _sync_creation_form_cache(config_key: str = "default") -> None:
    from apps.skill.services.creation_form_atomic_sync import sync_overrides_cache

    sync_overrides_cache(config_key)
    try:
        from apps.skill.config.portal.creation_form import CreationFormOverrideService

        CreationFormOverrideService._clear_catalog_cache()
    except Exception:  # noqa: BLE001
        pass


class CreationFormAtomicAdminMixin:
    list_filter = ["config_key", "is_active"]
    ordering = ["config_key", "sort_order"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _sync_creation_form_cache(getattr(obj, "config_key", "default"))


@admin.register(CreationPlatform)
class CreationPlatformAdmin(CreationFormAtomicAdminMixin, admin.ModelAdmin):
    list_display = ["config_key", "item_key", "name", "sort_order", "is_active"]
    search_fields = ["item_key", "name"]


@admin.register(CreationBudgetLevel)
class CreationBudgetLevelAdmin(CreationFormAtomicAdminMixin, admin.ModelAdmin):
    list_display = ["config_key", "item_key", "name", "sort_order", "is_active"]
    search_fields = ["item_key", "name"]


@admin.register(CreationEntry)
class CreationEntryAdmin(CreationFormAtomicAdminMixin, admin.ModelAdmin):
    list_display = ["config_key", "item_key", "name", "sort_order", "is_active"]
    search_fields = ["item_key", "name"]


@admin.register(CreationEntryProfile)
class CreationEntryProfileAdmin(admin.ModelAdmin):
    list_display = ["config_key", "entry_key", "is_active"]
    list_filter = ["config_key", "is_active"]
    search_fields = ["entry_key"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _sync_creation_form_cache(obj.config_key)


@admin.register(FormatVariant)
class FormatVariantAdmin(CreationFormAtomicAdminMixin, admin.ModelAdmin):
    list_display = ["config_key", "item_key", "name", "schema_key", "sort_order", "is_active"]
    search_fields = ["item_key", "name"]


@admin.register(CreationThemeEntry)
class CreationThemeEntryAdmin(admin.ModelAdmin):
    list_display = ["config_key", "theme_key", "display_name", "is_enabled", "sort_order"]
    list_filter = ["config_key", "is_enabled"]
    search_fields = ["theme_key", "display_name"]
    ordering = ["config_key", "sort_order"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _sync_creation_form_cache(obj.config_key)


@admin.register(EpisodeSettingsConfig)
class EpisodeSettingsConfigAdmin(admin.ModelAdmin):
    list_display = ["config_key", "min_episodes", "max_episodes", "default_episodes", "duration_minutes"]
    search_fields = ["config_key"]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        _sync_creation_form_cache(obj.config_key)


@admin.register(CreationFormOverrideConfig)
class CreationFormOverrideConfigAdmin(admin.ModelAdmin):
    list_display = ["config_key", "updated_at"]
    search_fields = ["config_key"]
    readonly_fields = ["updated_at"]
    actions = ["sync_atomic_to_json_cache", "import_json_to_atomic"]
    fieldsets = (
        ("配置键", {"fields": ("config_key",)}),
        ("JSON 缓存（只读参考）", {"fields": ("overrides", "episode_settings"), "classes": ("collapse",)}),
        ("时间戳", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )

    @admin.action(description="原子表 → overrides JSON 缓存")
    def sync_atomic_to_json_cache(self, request, queryset):
        count = 0
        for row in queryset:
            _sync_creation_form_cache(row.config_key)
            count += 1
        self.message_user(request, f"已同步 {count} 条配置的 JSON 缓存。")

    @admin.action(description="overrides JSON → 原子子表")
    def import_json_to_atomic(self, request, queryset):
        from apps.skill.services.creation_form_atomic_sync import migrate_from_overrides

        total = 0
        for row in queryset:
            result = migrate_from_overrides(config_key=row.config_key, overwrite=False)
            total += int(result.get("created") or 0)
        self.message_user(request, f"已从 JSON 导入/更新 {total} 条原子行。")
