# -*- coding: utf-8 -*-
"""Drama Skills Django Admin 注册"""
from django.contrib import admin

from apps.drama.models import (
    DramaEpisodeArtifact,
    DramaEpisodeQuality,
    DramaEpisodePlan,
    DramaGenerationPlan,
    DramaRoleExecution,
)


@admin.register(DramaRoleExecution)
class DramaRoleExecutionAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "project",
        "agent_name_zh",
        "status",
        "total_tokens",
        "cost_cents",
        "elapsed_seconds",
        "created_at",
    ]
    list_filter = ["status", "agent_id", "created_at"]
    search_fields = ["project__title", "agent_id", "agent_name_zh", "error_message"]
    readonly_fields = [
        "id",
        "project",
        "agent_id",
        "agent_name_zh",
        "input_artifacts",
        "output_artifacts",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "cost_cents",
        "elapsed_seconds",
        "llm_provider",
        "llm_model",
        "started_at",
        "finished_at",
        "created_at",
    ]
    list_select_related = ["project"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DramaEpisodeArtifact)
class DramaEpisodeArtifactAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "episode_number",
        "artifact_key",
        "version",
        "word_count",
        "quality_score",
        "produced_by_agent",
        "updated_at",
    ]
    list_filter = ["artifact_key", "produced_by_agent", "updated_at"]
    search_fields = ["project__title", "diff_summary"]
    readonly_fields = [
        "id",
        "project",
        "episode_number",
        "artifact_key",
        "version",
        "content",
        "diff_summary",
        "produced_by_agent",
        "quality_score",
        "word_count",
        "created_at",
        "updated_at",
    ]
    list_select_related = ["project"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DramaEpisodeQuality)
class DramaEpisodeQualityAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "episode_number",
        "get_overall_score",
        "get_grade",
        "evaluated_by_agent",
        "updated_at",
    ]
    list_filter = ["evaluated_by_agent", "updated_at"]
    search_fields = ["project__title", "summary"]
    readonly_fields = [
        "id",
        "project",
        "episode_number",
        "scores",
        "issues",
        "word_count_result",
        "summary",
        "evaluated_by_agent",
        "created_at",
        "updated_at",
    ]
    list_select_related = ["project"]
    date_hierarchy = "created_at"

    @admin.display(description="总分")
    def get_overall_score(self, obj):
        return obj.get_overall_score()

    @admin.display(description="等级")
    def get_grade(self, obj):
        return obj.get_grade()

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DramaEpisodePlan)
class DramaEpisodePlanAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "episode_number",
        "status",
        "quality_score",
        "quality_gate_passed",
        "rewrite_count",
        "batch_number",
        "actual_tokens",
        "updated_at",
    ]
    list_filter = ["status", "quality_gate_passed", "batch_number", "updated_at"]
    search_fields = ["project__title"]
    readonly_fields = [
        "id",
        "project",
        "episode_number",
        "status",
        "quality_score",
        "quality_gate_threshold",
        "quality_gate_passed",
        "rewrite_count",
        "max_rewrites",
        "batch_number",
        "estimated_tokens",
        "actual_tokens",
        "started_at",
        "finished_at",
        "created_at",
        "updated_at",
    ]
    list_select_related = ["project"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(DramaGenerationPlan)
class DramaGenerationPlanAdmin(admin.ModelAdmin):
    list_display = [
        "project",
        "status",
        "batch_size",
        "total_batches",
        "completed_batches",
        "current_batch",
        "quality_gate_score",
        "last_completed_episode",
        "updated_at",
    ]
    list_filter = ["status", "quality_gate_enabled", "auto_proceed_on_pass", "updated_at"]
    search_fields = ["project__title"]
    readonly_fields = [
        "id",
        "project",
        "status",
        "batch_size",
        "total_batches",
        "completed_batches",
        "current_batch",
        "quality_gate_enabled",
        "quality_gate_score",
        "auto_proceed_on_pass",
        "token_budget",
        "tokens_used",
        "last_completed_episode",
        "avg_tokens_per_episode",
        "estimated_total_minutes",
        "created_at",
        "updated_at",
    ]
    list_select_related = ["project"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
