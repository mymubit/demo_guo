# -*- coding: utf-8 -*-
"""Agent 模块 Django Admin。"""
from django.contrib import admin
from django.utils.html import format_html

from apps.agent.models import (
    ReviewGradeThreshold,
    ReviewScoringConfig,
    ReviewScoringDimension,
    ReviewScoringPreset,
)


class ReviewScoringDimensionInline(admin.TabularInline):
    model = ReviewScoringDimension
    extra = 0
    fields = ["dimension_key", "weight", "sort_order"]
    ordering = ["sort_order", "dimension_key"]


class ReviewGradeThresholdInline(admin.TabularInline):
    model = ReviewGradeThreshold
    extra = 0
    fields = ["grade", "min_score", "sort_order"]
    ordering = ["sort_order", "grade"]


@admin.register(ReviewScoringPreset)
class ReviewScoringPresetAdmin(admin.ModelAdmin):
    inlines = [ReviewScoringDimensionInline, ReviewGradeThresholdInline]
    list_display = ["preset_id", "name", "active_badge", "pass_threshold", "min_sub_item_score", "updated_at"]
    list_filter = ["is_active"]
    search_fields = ["preset_id", "name"]
    ordering = ["preset_id"]
    actions = ["activate_selected"]

    @admin.display(description="默认")
    def active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold">是</span>')
        return "否"

    @admin.action(description="设为默认预设（取消其他 active）")
    def activate_selected(self, request, queryset):
        if queryset.count() != 1:
            self.message_user(request, "请仅选择一条预设设为默认。", level="error")
            return
        preset = queryset.first()
        ReviewScoringPreset.objects.exclude(pk=preset.pk).update(is_active=False)
        preset.is_active = True
        preset.save(update_fields=["is_active", "updated_at"])
        self.message_user(request, f"已将「{preset.name}」设为默认审查评分预设。")


@admin.register(ReviewScoringConfig)
class ReviewScoringConfigAdmin(admin.ModelAdmin):
    list_display = ["config_key", "pass_threshold", "min_sub_item_score", "updated_at"]
    search_fields = ["config_key"]
    readonly_fields = ["updated_at"]
    fieldsets = (
        ("基础", {"fields": ("config_key", "pass_threshold", "min_sub_item_score")}),
        ("JSON 兜底", {"fields": ("weights", "grade_thresholds")}),
        ("时间戳", {"fields": ("updated_at",), "classes": ("collapse",)}),
    )
