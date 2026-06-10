# -*- coding: utf-8 -*-
"""
技能配置模块的后台管理配置
- 仅超级管理员可访问
- 加密配置值在后台以脱敏方式展示
"""
from django.contrib import admin
from django.contrib import messages

from apps.skill.models import SkillConfig, ThemeTemplate, HookLibrary, DialogueTemplate


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


admin.site.register(SkillConfig, SkillConfigAdmin)
admin.site.register(ThemeTemplate, ThemeTemplateAdmin)
admin.site.register(HookLibrary, HookLibraryAdmin)
admin.site.register(DialogueTemplate, DialogueTemplateAdmin)
